from sqlalchemy.orm import Session
from datetime import datetime
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction
from app.services.diagnosis_service import DiagnosisService
from app.services.customer_analysis_service import CustomerAnalysisService
from app.services.strategy_service import StrategyService
from app.services.simulation_engine import SimulationEngine
from app.schemas.recovery_result import RecoveryResult, ActionResultSchema
from app.policies.policy_engine import PolicyEngine
from app.services.explainability_service import ExplainabilityService

class RecoveryEngine:
    def __init__(self):
        self.diagnosis_service = DiagnosisService()
        self.customer_analysis_service = CustomerAnalysisService()
        self.strategy_service = StrategyService()
        self.simulation_engine = SimulationEngine()
        self.policy_engine = PolicyEngine()
        self.explainability_service = ExplainabilityService()

    def process_case(self, case_id: str, db: Session) -> RecoveryResult:
        """
        Coordinates the recovery workflow for a single case. Loads context,
        runs analysis/diagnosis services, evaluates policies, and conditionally
        executes simulated actions based on policy decisions.
        """
        # Load Case
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
        if not case:
            raise ValueError(f"Recovery case {case_id} not found.")

        # Load Payment and Customer
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        customer = db.query(Customer).filter(Customer.customer_id == payment.customer_id).first()

        # Generate diagnostics profiling
        diagnosis = self.diagnosis_service.diagnose_payment(payment)
        analysis = self.customer_analysis_service.analyze_customer(customer)
        strategy = self.strategy_service.determine_strategy(
            diagnosis, analysis, payment.amount, payment.retry_count, payment.reminder_count
        )

        # Run Policy Engine Evaluation
        policy = self.policy_engine.evaluate(
            case, payment, customer, diagnosis, analysis, strategy
        )

        sim_result = None

        if policy.action_allowed:
            # 1. Update recovery case intelligence fields in DB
            case.recovery_probability = strategy.recovery_probability
            case.expected_recovery_value = strategy.expected_recovery_value
            case.estimated_action_cost = strategy.estimated_action_cost
            case.current_strategy = strategy.recommended_action
            case.updated_at = datetime.utcnow()
            db.commit()

            # 2. Run execution via RecoveryExecutionService
            from app.services.recovery_execution_service import RecoveryExecutionService
            execution_service = RecoveryExecutionService()
            db_action = execution_service.execute_recovery(case.case_id, strategy.recommended_action, db)
            
            sim_result = ActionResultSchema(
                action=db_action.action_type,
                result="SUCCESS" if db_action.status == "SUCCEEDED" else ("STOPPED" if db_action.status == "BLOCKED" else db_action.status),
                recovered_amount=db_action.recovered_amount
            )
        else:
            # Action was blocked, stopped, or routed to HITL by policy engine
            if policy.decision in ["STOPPED", "BLOCKED"]:
                case.status = "STOPPED"
                # If payment is already recovered, ensure sync
                if payment.is_recovered:
                    case.status = "RECOVERED"
            elif policy.decision == "HITL_REQUIRED":
                case.status = "WAITING_FOR_APPROVAL"
                case.requires_human_approval = True
                # Ensure payment disputes sync with case state
                if payment.is_disputed:
                    case.status = "ESCALATED"

        # Generate decision explanation
        explanation = self.explainability_service.generate_explanation(
            case=case,
            payment=payment,
            customer=customer,
            diagnosis=diagnosis,
            customer_analysis=analysis,
            strategy=strategy,
            policy_decision=policy.decision,
            triggered_rules=policy.triggered_rules
        )
        case.explanation_json = explanation

        db.commit()
        db.refresh(case)
        db.refresh(payment)

        return RecoveryResult(
            case_id=case_id,
            status=case.status,
            diagnosis=diagnosis,
            customer_analysis=analysis,
            strategy=strategy,
            policy=policy,
            action_result=sim_result,
            explanation=explanation
        )
