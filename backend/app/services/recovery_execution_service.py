import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.models.recovery_case import RecoveryCase, RecoveryCaseStatus
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.policies.policy_engine import PolicyEngine
from app.services.diagnosis_service import DiagnosisService
from app.services.customer_analysis_service import CustomerAnalysisService
from app.services.strategy_service import StrategyService
from app.services.providers.simulation import SimulatedRecoveryProvider
from app.services.providers.future_payment import FuturePaymentProviderAdapter

logger = logging.getLogger("recoverai.execution_service")

# Strict lifecycle transitions mapping
VALID_TRANSITIONS = {
    "REQUESTED": ["VALIDATED", "BLOCKED", "CANCELLED"],
    "VALIDATED": ["DISPATCHED", "BLOCKED", "CANCELLED"],
    "DISPATCHED": ["PROCESSING", "FAILED", "CANCELLED"],
    "PROCESSING": ["SUCCEEDED", "FAILED", "BLOCKED", "CANCELLED"],
    "SUCCEEDED": [],
    "FAILED": [],
    "BLOCKED": [],
    "CANCELLED": []
}

class RecoveryExecutionService:
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.diagnosis_service = DiagnosisService()
        self.customer_analysis_service = CustomerAnalysisService()
        self.strategy_service = StrategyService()
        
    def transition_status(self, action: RecoveryAction, new_status: str, db: Session):
        """
        Validates and transitions execution status, enforcing strict lifecycle constraints.
        """
        current = action.status
        allowed = VALID_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid state transition requested: {current} -> {new_status}")
        
        action.status = new_status
        db.commit()
        logger.info(f"Execution {action.action_id} transitioned: {current} -> {new_status}")

    def execute_recovery(self, case_id: str, strategy: str, db: Session) -> RecoveryAction:
        """
        Coordinates the recovery attempt: checks idempotency/concurrency,
        revalidates policy, dispatches to provider, handles results.
        """
        # Load core domain objects
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found.")
            
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        customer = db.query(Customer).filter(Customer.customer_id == payment.customer_id).first()

        # 1. Concurrency Protection: check for non-terminal attempts currently running
        active_attempt = db.query(RecoveryAction).filter(
            RecoveryAction.case_id == case_id,
            RecoveryAction.status.in_(["REQUESTED", "VALIDATED", "DISPATCHED", "PROCESSING"])
        ).first()
        if active_attempt:
            logger.warning(f"Concurrent recovery attempt blocked. Execution {active_attempt.action_id} is in progress.")
            return active_attempt

        # 2. Idempotency Check: check if the latest attempt for this case matches the same strategy
        latest_action = db.query(RecoveryAction).filter(
            RecoveryAction.case_id == case_id
        ).order_by(RecoveryAction.attempt_number.desc()).first()
        
        if latest_action and latest_action.action_type == strategy:
            logger.info(f"Duplicate/idempotent request detected. Returning existing action: {latest_action.action_id}")
            return latest_action

        # Enforce terminal case state block
        if case.status in ["RECOVERED", "STOPPED"]:
            raise ValueError(f"Cannot execute recovery for case {case_id} in terminal state: {case.status}")

        attempt_number = db.query(RecoveryAction).filter(RecoveryAction.case_id == case_id).count() + 1
        idempotency_key = f"IDEM-{case_id}-{strategy}-{attempt_number}"

        # 3. Create the Execution attempt (REQUESTED)
        action_id = f"ACT-{case_id}-{attempt_number}"
        action = RecoveryAction(
            action_id=action_id,
            case_id=case_id,
            action_type=strategy,
            status="REQUESTED",
            attempt_number=attempt_number,
            idempotency_key=idempotency_key,
            requested_at=datetime.utcnow(),
            simulation_mode=settings.SIMULATION_MODE,
            execution_context={
                "expected_strategy": case.metadata_json.get("expected_strategy") if case.metadata_json else None,
                "expected_outcome": case.metadata_json.get("expected_outcome") if case.metadata_json else None,
                "recovered_amount": case.metadata_json.get("recovered_amount") if case.metadata_json else None,
                "recovery_probability": case.recovery_probability
            } if case.metadata_json else {}
        )
        db.add(action)
        db.commit()

        # Log REQUESTED audit event
        self._log_audit(case_id, "RECOVERY_EXECUTION_REQUESTED", "SYSTEM", "RecoveryExecutionService", 
                          f"Recovery execution requested for attempt #{attempt_number} using strategy {strategy}.", 
                          {"idempotency_key": idempotency_key}, db)

        # 4. Pre-execution Policy Revalidation
        try:
            diagnosis = self.diagnosis_service.diagnose_payment(payment)
            analysis = self.customer_analysis_service.analyze_customer(customer)
            strat_res = self.strategy_service.determine_strategy(
                diagnosis, analysis, payment.amount, payment.retry_count, payment.reminder_count
            )
            policy = self.policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strat_res)
            action.policy_decision = policy.decision
            db.commit()
            
            self._log_audit(case_id, "RECOVERY_EXECUTION_VALIDATED", "SYSTEM", "PolicyEngine", 
                              f"Policy validation evaluated. Outcome: {policy.decision}.", 
                              {"decision": policy.decision, "action_allowed": policy.action_allowed}, db)

            if not policy.action_allowed:
                # If it was blocked by HITL rules but we have a valid human approval, we can bypass it
                soft_rules = {"HIGH_VALUE_TRANSACTION", "LOW_DIAGNOSIS_CONFIDENCE", "MULTIPLE_FAILED_ATTEMPTS"}
                is_only_soft = policy.decision == "HITL_REQUIRED" and all(r in soft_rules for r in policy.triggered_rules)
                
                # Check if human approval exists
                from app.models.approval import HumanApproval, ApprovalDecision
                latest_approval = db.query(HumanApproval).filter(
                    HumanApproval.case_id == case_id
                ).order_by(HumanApproval.resolved_at.desc()).first()
                has_human_approval = latest_approval and latest_approval.decision == ApprovalDecision.APPROVED.value
                
                if is_only_soft and has_human_approval:
                    logger.info(f"Bypassing soft policy block for case {case_id} due to human approval.")
                else:
                    self.transition_status(action, "BLOCKED", db)
                    
                    # Update case statuses based on policy engine rejection
                    if policy.decision == "HITL_REQUIRED":
                        case.status = "WAITING_FOR_APPROVAL"
                        case.requires_human_approval = True
                    elif policy.decision in ["STOPPED", "BLOCKED"]:
                        case.status = "STOPPED"
                    db.commit()
                    
                    self._log_audit(case_id, "RECOVERY_EXECUTION_BLOCKED", "SYSTEM", "RecoveryExecutionService",
                                      f"Execution blocked by policy engine. Transitioned case status to {case.status}.", {}, db)
                    return action

            # If allowed, transition to VALIDATED
            self.transition_status(action, "VALIDATED", db)
            
        except Exception as e:
            logger.error(f"Policy revalidation failed: {str(e)}")
            self.transition_status(action, "CANCELLED", db)
            action.result = f"Policy validation failed: {str(e)}"
            db.commit()
            return action

        # 5. Dispatch & Execution
        try:
            self.transition_status(action, "DISPATCHED", db)
            self._log_audit(case_id, "RECOVERY_EXECUTION_DISPATCHED", "SYSTEM", "RecoveryExecutionService",
                              f"Dispatched execution request to provider adapter.", {}, db)
            
            self.transition_status(action, "PROCESSING", db)
            
            # Select Provider Adapter
            if settings.SIMULATION_MODE:
                provider = SimulatedRecoveryProvider()
            else:
                provider = FuturePaymentProviderAdapter()
                
            # Perform simulated/real execution
            provider_res = provider.execute_recovery_action(
                case_id=case_id,
                strategy=strategy,
                amount=payment.amount,
                attempt_number=attempt_number,
                execution_context=action.execution_context
            )
            
            # Handle normalized results
            action.result = provider_res.message
            action.executed_at = datetime.utcnow()
            action.recovered_amount = provider_res.recovered_amount
            db.commit()

            # Enforce transition to terminal state (SUCCEEDED / FAILED / BLOCKED / CANCELLED)
            self.transition_status(action, provider_res.status, db)

            # Update business states based on Provider response
            if provider_res.status == "SUCCEEDED" and provider_res.recovered_amount > 0:
                # Revenue Recovery Success
                case.status = "RECOVERED"
                case.requires_human_approval = False
                payment.is_recovered = True
                payment.status = "RECOVERED"
                db.commit()
                
                self._log_audit(case_id, "RECOVERY_EXECUTION_SUCCEEDED", "SYSTEM", "RecoveryExecutionService",
                                  f"Recovery attempt succeeded! Recovered amount: {payment.currency} {provider_res.recovered_amount}.", 
                                  {"recovered_amount": provider_res.recovered_amount, "reference": provider_res.provider_reference}, db)
            else:
                # Recovery failure / block / retry needed
                if strategy == "ESCALATE_TO_HUMAN":
                    case.status = "ESCALATED"
                    db.commit()
                    self._log_audit(case_id, "RECOVERY_EXECUTION_FAILED", "SYSTEM", "RecoveryExecutionService",
                                      f"Execution escalated case to human review queue.", {}, db)
                elif provider_res.status == "BLOCKED":
                    case.status = "STOPPED"
                    db.commit()
                    self._log_audit(case_id, "RECOVERY_EXECUTION_BLOCKED", "SYSTEM", "RecoveryExecutionService",
                                      f"Execution returned blocked status: {provider_res.message}.", {}, db)
                else:
                    # Action execution complete, but payment recovery outcome failed or needs retry
                    if strategy in ["SMART_RETRY", "WAIT_AND_RETRY"]:
                        payment.retry_count += 1
                    else:
                        payment.reminder_count += 1
                    
                    if strategy == "WAIT_AND_RETRY":
                        case.status = "SCHEDULED"
                    else:
                        case.status = "PROCESSING"
                    db.commit()
                    
                    self._log_audit(case_id, "RECOVERY_EXECUTION_FAILED", "SYSTEM", "RecoveryExecutionService",
                                      f"Execution finished, but payment was not recovered. Status: {case.status}. Error: {provider_res.message}.", 
                                      {"recoverable": provider_res.recoverable}, db)
            
            db.refresh(case)
            db.refresh(payment)
            return action

        except Exception as e:
            logger.error(f"Execution failed due to error: {str(e)}")
            # Transition to terminal FAILED state
            if action.status != "FAILED":
                action.status = "FAILED"
            action.result = f"Provider communication failure: {str(e)}"
            db.commit()
            
            self._log_audit(case_id, "RECOVERY_EXECUTION_FAILED", "SYSTEM", "RecoveryExecutionService",
                              f"Technical execution error: {str(e)}.", {}, db)
            return action

    def _log_audit(self, case_id: str, event_type: str, actor_type: str, actor_name: str, summary: str, metadata: dict, db: Session):
        audit_id = f"AUD-{case_id}-{uuid.uuid4().hex[:6]}"
        db_audit = AuditLog(
            audit_id=audit_id,
            case_id=case_id,
            actor_type=actor_type,
            actor_name=actor_name,
            event_type=event_type,
            decision_summary=summary[:255] if summary else None,
            metadata_json=metadata,
            timestamp=datetime.utcnow()
        )
        db.add(db_audit)
        db.commit()
