from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from app.db.database import get_db
from app.services.recovery_engine import RecoveryEngine
from app.services.metrics_service import MetricsService
from app.schemas.recovery_result import RecoveryResult
from app.schemas.graph_run import GraphRunResultSchema
from app.schemas.custom_case import CreateCustomCaseRequest, CreateCustomCaseResponse
from app.graphs.recovery_graph import run_recovery_graph
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/cases", tags=["cases"])

@router.post("", response_model=CreateCustomCaseResponse)
def create_custom_case(payload: CreateCustomCaseRequest, db: Session = Depends(get_db)):
    """
    Creates a new custom failed payment and recovery case with personalized revenue,
    customer LTV/segment, and failure parameters, and optionally triggers the multi-agent
    recovery pipeline immediately.
    """
    try:
        # Generate unique IDs
        unique_suffix = uuid.uuid4().hex[:6].upper()
        case_id = f"REC-USER-{unique_suffix}"
        payment_id = f"PAY-USER-{unique_suffix}"
        customer_id = f"CUST-USER-{unique_suffix}"
        
        # Calculate or default customer metrics
        avg_amt = payload.average_payment_amount
        if avg_amt is None:
            if (payload.successful_payments or 0) > 0 and (payload.customer_ltv or 0) > 0:
                avg_amt = payload.customer_ltv / payload.successful_payments
            else:
                avg_amt = payload.amount
        
        # 1. Create and insert Customer
        customer = Customer(
            customer_id=customer_id,
            name=payload.customer_name or "Custom Customer",
            segment=payload.customer_segment or "RELIABLE",
            lifetime_value=payload.customer_ltv or 0.0,
            total_successful_payments=payload.successful_payments or 0,
            total_failed_payments=payload.failed_payments or 0,
            average_payment_amount=avg_amt,
            engagement_score=payload.engagement_score or 5.0,
            created_at=datetime.utcnow()
        )
        db.add(customer)
        db.commit()
        
        # 2. Create and insert Payment
        payment = Payment(
            payment_id=payment_id,
            customer_id=customer_id,
            amount=payload.amount,
            currency=payload.currency.upper(),
            payment_method=payload.payment_method.upper(),
            status="FAILED",
            failure_code=payload.failure_code,
            retry_count=payload.retry_count,
            reminder_count=payload.reminder_count,
            is_disputed=payload.is_disputed,
            is_recovered=False,
            created_at=datetime.utcnow()
        )
        db.add(payment)
        db.commit()
        
        # 3. Create and insert RecoveryCase
        recovery_case = RecoveryCase(
            case_id=case_id,
            payment_id=payment_id,
            batch_id=None,
            status="PENDING",
            current_strategy=None,
            recovery_probability=0.0,
            expected_recovery_value=0.0,
            estimated_action_cost=0.0,
            requires_human_approval=False,
            metadata_json={
                "source": "CUSTOM_INTAKE",
                "custom_feed": True,
                "customer_name": payload.customer_name,
                "initial_revenue": payload.amount
            },
            created_at=datetime.utcnow()
        )
        db.add(recovery_case)
        db.commit()
        
        # 4. Audit Log
        audit = AuditLog(
            audit_id=f"AUD-{case_id}-{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            batch_id=None,
            actor_type="USER",
            actor_name="DashboardUser",
            event_type="CASE_CREATED",
            decision_summary=f"Personalized failed payment fed with revenue ₹{payload.amount:,.2f} for {payload.customer_name}.",
            metadata_json={
                "amount": payload.amount,
                "currency": payload.currency,
                "customer_segment": payload.customer_segment,
                "failure_code": payload.failure_code
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        
        graph_result = None
        if payload.auto_run:
            result_state = run_recovery_graph(case_id, db)
            graph_result = GraphRunResultSchema(
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
            db.refresh(recovery_case)
        
        return CreateCustomCaseResponse(
            case_id=case_id,
            payment_id=payment_id,
            customer_id=customer_id,
            status=recovery_case.status,
            amount=payment.amount,
            currency=payment.currency,
            message="Custom recovery case created successfully",
            graph_result=graph_result
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create custom case: {str(e)}")


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
