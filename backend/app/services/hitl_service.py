from sqlalchemy.orm import Session
from datetime import datetime
from app.models.approval import HumanApproval, ApprovalDecision
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.services.diagnosis_service import DiagnosisService
from app.services.customer_analysis_service import CustomerAnalysisService
from app.services.strategy_service import StrategyService
from app.graphs.recovery_graph import app_graph

class HITLService:
    def get_pending_approvals(self, db: Session):
        approvals = db.query(HumanApproval).filter(
            HumanApproval.decision == ApprovalDecision.PENDING.value
        ).all()
        
        results = []
        for app in approvals:
            case = db.query(RecoveryCase).filter(RecoveryCase.case_id == app.case_id).first()
            if not case:
                continue
            payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
            if not payment:
                continue
                
            results.append({
                "case_id": case.case_id,
                "payment_amount": payment.amount,
                "recommended_action": case.current_strategy or "UNKNOWN",
                "recovery_probability": case.recovery_probability,
                "triggered_rules": case.metadata_json.get("triggered_rules", []) if case.metadata_json else [],
                "created_at": app.created_at.isoformat(),
                "explanation_json": case.explanation_json
            })
            
        # Predictable sorting: Highest payment value first
        results.sort(key=lambda x: x["payment_amount"], reverse=True)
        return results

    def get_approval_context(self, case_id: str, db: Session):
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found.")
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        customer = db.query(Customer).filter(Customer.customer_id == payment.customer_id).first()
        
        diagnosis = DiagnosisService().diagnose_payment(payment)
        analysis = CustomerAnalysisService().analyze_customer(customer)
        strategy = StrategyService().determine_strategy(
            diagnosis, analysis, payment.amount, payment.retry_count, payment.reminder_count
        )
        
        from app.policies.policy_engine import PolicyEngine
        policy = PolicyEngine().evaluate(case, payment, customer, diagnosis, analysis, strategy)
        
        return {
            "case_id": case.case_id,
            "payment": {
                "amount": payment.amount,
                "status": payment.status
            },
            "customer_analysis": {
                "customer_quality_score": analysis.customer_quality_score,
                "payment_reliability_score": analysis.payment_reliability_score
            },
            "diagnosis": {
                "failure_category": diagnosis.failure_category,
                "confidence": diagnosis.confidence
            },
            "strategy": {
                "recommended_action": strategy.recommended_action,
                "recovery_probability": strategy.recovery_probability,
                "expected_recovery_value": strategy.expected_recovery_value
            },
            "policy": {
                "decision": policy.decision,
                "triggered_rules": policy.triggered_rules,
                "reasons": policy.reasons
            },
            "explanation_json": case.explanation_json
        }

    def approve_case(self, case_id: str, reviewer_id: str, reason: str, db: Session):
        approval = db.query(HumanApproval).filter(
            HumanApproval.case_id == case_id,
            HumanApproval.decision == ApprovalDecision.PENDING.value
        ).first()
        
        if not approval:
            decided = db.query(HumanApproval).filter(
                HumanApproval.case_id == case_id
            ).order_by(HumanApproval.created_at.desc()).first()
            if decided:
                raise ValueError(f"Case {case_id} has already been resolved with decision: {decided.decision}.")
            raise ValueError(f"No pending approval request found for case {case_id}.")
            
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
        if case.status in ["RECOVERED", "STOPPED", "FAILED"]:
            raise ValueError(f"Cannot approve case {case_id} because it is in a terminal state: {case.status}.")
            
        # Update Approval Record
        approval.decision = ApprovalDecision.APPROVED.value
        approval.reviewer = reviewer_id
        approval.reason = reason[:255] if reason else None
        approval.resolved_at = datetime.utcnow()
        
        # Log to AuditLog
        import uuid
        audit_id = f"AUD-{case_id}-{uuid.uuid4().hex[:6]}"
        db_audit = AuditLog(
            audit_id=audit_id,
            case_id=case_id,
            actor_type="HUMAN",
            actor_name=reviewer_id,
            event_type="HUMAN_APPROVAL",
            decision_summary=f"Approved by {reviewer_id}. Reason: {reason}",
            timestamp=datetime.utcnow()
        )
        db.add(db_audit)
        db.commit()
        
        # Invoke LangGraph workflow with human decision set
        initial_state = {
            "case_id": case_id,
            "payment_data": None,
            "customer_data": None,
            "diagnosis": None,
            "customer_analysis": None,
            "strategy": None,
            "policy": None,
            "action_result": None,
            "final_status": None,
            "agent_trace": [],
            "errors": [],
            "human_decision": {
                "decision": "APPROVED",
                "reviewer_id": reviewer_id,
                "reason": reason
            }
        }
        
        result_state = app_graph.invoke(
            initial_state,
            config={"configurable": {"db": db}}
        )
        
        return result_state

    def reject_case(self, case_id: str, reviewer_id: str, reason: str, db: Session):
        approval = db.query(HumanApproval).filter(
            HumanApproval.case_id == case_id,
            HumanApproval.decision == ApprovalDecision.PENDING.value
        ).first()
        
        if not approval:
            decided = db.query(HumanApproval).filter(
                HumanApproval.case_id == case_id
            ).order_by(HumanApproval.created_at.desc()).first()
            if decided:
                raise ValueError(f"Case {case_id} has already been resolved with decision: {decided.decision}.")
            raise ValueError(f"No pending approval request found for case {case_id}.")
            
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
        if case.status in ["RECOVERED", "STOPPED", "FAILED"]:
            raise ValueError(f"Cannot reject case {case_id} because it is in a terminal state: {case.status}.")
            
        # Update Approval Record
        approval.decision = ApprovalDecision.REJECTED.value
        approval.reviewer = reviewer_id
        approval.reason = reason[:255] if reason else None
        approval.resolved_at = datetime.utcnow()
        
        # Log to AuditLog
        import uuid
        audit_id = f"AUD-{case_id}-{uuid.uuid4().hex[:6]}"
        db_audit = AuditLog(
            audit_id=audit_id,
            case_id=case_id,
            actor_type="HUMAN",
            actor_name=reviewer_id,
            event_type="HUMAN_REJECTION",
            decision_summary=f"Rejected by {reviewer_id}. Reason: {reason}",
            timestamp=datetime.utcnow()
        )
        db.add(db_audit)
        db.commit()
        
        # Invoke LangGraph workflow with human decision set
        initial_state = {
            "case_id": case_id,
            "payment_data": None,
            "customer_data": None,
            "diagnosis": None,
            "customer_analysis": None,
            "strategy": None,
            "policy": None,
            "action_result": None,
            "final_status": None,
            "agent_trace": [],
            "errors": [],
            "human_decision": {
                "decision": "REJECTED",
                "reviewer_id": reviewer_id,
                "reason": reason
            }
        }
        
        result_state = app_graph.invoke(
            initial_state,
            config={"configurable": {"db": db}}
        )
        
        return result_state
