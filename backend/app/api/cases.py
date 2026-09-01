from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.recovery_engine import RecoveryEngine
from app.services.metrics_service import MetricsService
from app.schemas.recovery_result import RecoveryResult
from app.schemas.graph_run import GraphRunResultSchema
from app.graphs.recovery_graph import run_recovery_graph
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction

router = APIRouter(prefix="/api/cases", tags=["cases"])

@router.post("/{case_id}/run", response_model=GraphRunResultSchema)
def run_case_graph(case_id: str, db: Session = Depends(get_db)):
    """
    Triggers the LangGraph-based multi-agent workflow for a single case.
    """
    try:
        result_state = run_recovery_graph(case_id, db)
        if result_state.get("errors") and not result_state.get("payment_data"):
            raise ValueError(result_state["errors"][0])
            
        return GraphRunResultSchema(
            case_id=result_state["case_id"],
            workflow_status="completed" if not result_state.get("errors") else "failed",
            diagnosis=result_state.get("diagnosis"),
            customer_analysis=result_state.get("customer_analysis"),
            strategy=result_state.get("strategy"),
            policy=result_state.get("policy"),
            action_result=result_state.get("action_result"),
            final_status=result_state.get("final_status") or "FAILED",
            agent_trace=result_state.get("agent_trace", []),
            errors=result_state.get("errors", [])
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph workflow execution failed: {str(e)}")

@router.post("/{case_id}/process", response_model=RecoveryResult)
def process_case(case_id: str, db: Session = Depends(get_db)):
    """
    Triggers end-to-end recovery processing for a single case.
    Runs diagnosis, profiles the customer, determines strategy,
    simulates outcome execution, and updates database records.
    """
    try:
        engine = RecoveryEngine()
        result = engine.process_case(case_id, db)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Case processing failed: {str(e)}")

@router.post("/{case_id}/trigger_scheduled", response_model=GraphRunResultSchema)
def trigger_scheduled_retry(case_id: str, db: Session = Depends(get_db)):
    """
    Manually triggers execution of a scheduled recovery action.
    """
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    if case.status != "SCHEDULED":
        raise HTTPException(status_code=400, detail=f"Case {case_id} is not in SCHEDULED status.")
        
    try:
        result_state = run_recovery_graph(case_id, db)
        if result_state.get("errors") and not result_state.get("payment_data"):
            raise ValueError(result_state["errors"][0])
            
        return GraphRunResultSchema(
            case_id=result_state["case_id"],
            workflow_status="completed" if not result_state.get("errors") else "failed",
            diagnosis=result_state.get("diagnosis"),
            customer_analysis=result_state.get("customer_analysis"),
            strategy=result_state.get("strategy"),
            policy=result_state.get("policy"),
            action_result=result_state.get("action_result"),
            final_status=result_state.get("final_status") or "FAILED",
            agent_trace=result_state.get("agent_trace", []),
            errors=result_state.get("errors", [])
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute scheduled action: {str(e)}")

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """
    Returns calculated recovery metrics derived from database state.
    """
    try:
        metrics_service = MetricsService()
        return metrics_service.calculate_metrics(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")

@router.get("")
def list_cases(db: Session = Depends(get_db)):
    """
    Returns a list of all recovery cases with their payments, actions, and metadata.
    """
    try:
        cases = db.query(RecoveryCase).all()
        res = []
        for case in cases:
            payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
            actions = db.query(RecoveryAction).filter(RecoveryAction.case_id == case.case_id).all()
            res.append({
                "case_id": case.case_id,
                "payment_id": case.payment_id,
                "batch_id": case.batch_id,
                "status": case.status,
                "current_strategy": case.current_strategy,
                "recovery_probability": case.recovery_probability,
                "expected_recovery_value": case.expected_recovery_value,
                "estimated_action_cost": case.estimated_action_cost,
                "requires_human_approval": case.requires_human_approval,
                "metadata_json": case.metadata_json,
                "explanation_json": case.explanation_json,
                "created_at": case.created_at.isoformat() if case.created_at else None,
                "updated_at": case.updated_at.isoformat() if case.updated_at else None,
                "payment": {
                    "payment_id": payment.payment_id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status,
                    "retry_count": payment.retry_count,
                    "reminder_count": payment.reminder_count,
                    "is_recovered": payment.is_recovered
                } if payment else None,
                "actions": [
                    {
                        "action_id": act.action_id,
                        "action_type": act.action_type,
                        "status": act.status,
                        "recovered_amount": act.recovered_amount,
                        "executed_at": act.executed_at.isoformat() if act.executed_at else None,
                        "attempt_number": act.attempt_number,
                        "idempotency_key": act.idempotency_key,
                        "requested_at": act.requested_at.isoformat() if act.requested_at else None,
                        "simulation_mode": act.simulation_mode,
                        "policy_decision": act.policy_decision,
                        "result": act.result
                    } for act in actions
                ]
            })
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cases: {str(e)}")

@router.get("/{case_id}")
def get_case_details(case_id: str, db: Session = Depends(get_db)):
    """
    Returns complete details for a single recovery case.
    """
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
    actions = db.query(RecoveryAction).filter(RecoveryAction.case_id == case.case_id).all()
    customer = db.query(Customer).filter(Customer.customer_id == payment.customer_id).first() if payment else None

    return {
        "case_id": case.case_id,
        "payment_id": case.payment_id,
        "batch_id": case.batch_id,
        "status": case.status,
        "current_strategy": case.current_strategy,
        "recovery_probability": case.recovery_probability,
        "expected_recovery_value": case.expected_recovery_value,
        "estimated_action_cost": case.estimated_action_cost,
        "requires_human_approval": case.requires_human_approval,
        "metadata_json": case.metadata_json,
        "explanation_json": case.explanation_json,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "payment": {
            "payment_id": payment.payment_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "retry_count": payment.retry_count,
            "reminder_count": payment.reminder_count,
            "is_recovered": payment.is_recovered,
            "customer": {
                "customer_id": customer.customer_id,
                "name": customer.name,
                "segment": customer.segment,
                "engagement_score": customer.engagement_score
            } if customer else None
        } if payment else None,
        "actions": [
            {
                "action_id": act.action_id,
                "action_type": act.action_type,
                "status": act.status,
                "recovered_amount": act.recovered_amount,
                "executed_at": act.executed_at.isoformat() if act.executed_at else None,
                "attempt_number": act.attempt_number,
                "idempotency_key": act.idempotency_key,
                "requested_at": act.requested_at.isoformat() if act.requested_at else None,
                "simulation_mode": act.simulation_mode,
                "policy_decision": act.policy_decision,
                "result": act.result
            } for act in actions
        ]
    }
