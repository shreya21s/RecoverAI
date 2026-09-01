import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult
from app.schemas.strategy import StrategyResult
from app.services.explainability_service import ExplainabilityService
from app.db.database import SessionLocal
from app.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    response = client.post("/api/demo/reset")
    assert response.status_code == 200

def test_explainability_service_direct():
    service = ExplainabilityService()
    
    # 1. Mock APPROVED Case context
    customer = Customer(
        customer_id="CUST-EXP",
        name="Reliable Customer",
        segment="RELIABLE",
        total_successful_payments=10,
        total_failed_payments=0,
        average_payment_amount=1000.0,
        engagement_score=9.0
    )
    payment = Payment(
        payment_id="PAY-EXP",
        customer_id="CUST-EXP",
        amount=1000.0,
        currency="INR",
        status="FAILED",
        failure_code="TEMPORARY_BANK_FAILURE",
        retry_count=0,
        reminder_count=0
    )
    case = RecoveryCase(
        case_id="REC-EXP",
        payment_id="PAY-EXP",
        status="PENDING"
    )
    diagnosis = DiagnosisResult(
        failure_category="TEMPORARY_FAILURE",
        confidence=0.95,
        evidence=[],
        recommended_direction="SMART_RETRY"
    )
    customer_analysis = CustomerAnalysisResult(
        customer_segment="RELIABLE",
        customer_quality_score=0.9,
        engagement_score=0.9,
        payment_reliability_score=0.95,
        historical_recovery_probability=0.9,
        evidence=[]
    )
    strategy = StrategyResult(
        recommended_action="SMART_RETRY",
        recovery_probability=0.9,
        expected_recovery_value=880.0,
        estimated_action_cost=20.0,
        reason="Temporary failure with high quality customer",
        alternative_actions=["WAIT_AND_RETRY"]
    )
    
    # Generate APPROVED explanation
    exp_approved = service.generate_explanation(
        case=case,
        payment=payment,
        customer=customer,
        diagnosis=diagnosis,
        customer_analysis=customer_analysis,
        strategy=strategy,
        policy_decision="APPROVED",
        triggered_rules=[]
    )
    
    assert exp_approved["selected_strategy"] == "SMART_RETRY"
    assert exp_approved["policy_explanation"]["decision"] == "APPROVED"
    assert exp_approved["override_details"]["is_overridden"] is False
    
    # Check factors
    factors = {f["factor"]: f for f in exp_approved["primary_factors"]}
    assert "Failure Category" in factors
    assert factors["Failure Category"]["impact"] == "positive"
    assert "Customer Quality" in factors
    assert factors["Customer Quality"]["impact"] == "positive"
    assert "Transaction Amount" in factors
    assert factors["Transaction Amount"]["impact"] == "positive"
    
    # Check counterfactuals for APPROVED
    assert len(exp_approved["counterfactuals"]) > 0
    assert any("MAX_RETRIES" in c["condition"] or "maximum limit" in c["condition"] for c in exp_approved["counterfactuals"])

    # 2. Mock STOPPED Case context (Max Retries)
    payment.retry_count = settings.MAX_RETRIES
    exp_stopped = service.generate_explanation(
        case=case,
        payment=payment,
        customer=customer,
        diagnosis=diagnosis,
        customer_analysis=customer_analysis,
        strategy=strategy,
        policy_decision="STOPPED",
        triggered_rules=["MAX_RETRIES_REACHED"]
    )
    assert exp_stopped["policy_explanation"]["decision"] == "STOPPED"
    assert "MAX_RETRIES_REACHED" in exp_stopped["policy_explanation"]["triggered_rules"]
    assert exp_stopped["override_details"]["is_overridden"] is True
    
    # Check counterfactual for max retries
    cf_stopped = exp_stopped["counterfactuals"]
    assert len(cf_stopped) > 0
    assert any("retry attempts" in cf["condition"] for cf in cf_stopped)

    # 3. Mock HITL Case context (High Value Transaction)
    payment.amount = settings.HITL_AMOUNT_THRESHOLD + 100
    payment.retry_count = 0
    exp_hitl = service.generate_explanation(
        case=case,
        payment=payment,
        customer=customer,
        diagnosis=diagnosis,
        customer_analysis=customer_analysis,
        strategy=strategy,
        policy_decision="HITL_REQUIRED",
        triggered_rules=["HIGH_VALUE_TRANSACTION"]
    )
    assert exp_hitl["policy_explanation"]["decision"] == "HITL_REQUIRED"
    assert "HIGH_VALUE_TRANSACTION" in exp_hitl["policy_explanation"]["triggered_rules"]
    
    # Check counterfactual for High Value Transaction
    cf_hitl = exp_hitl["counterfactuals"]
    assert len(cf_hitl) > 0
    assert any("transaction amount" in cf["condition"] for cf in cf_hitl)

def test_decision_explained_audit_log_and_api():
    # Run showcase case 1 (REC-DEMO-001) which executes fully and generates an explanation
    run_res = client.post("/api/cases/REC-DEMO-001/run")
    assert run_res.status_code == 200
    
    # Verify case detail API returns explanation
    detail_res = client.get("/api/cases/REC-DEMO-001")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["explanation_json"] is not None
    assert detail_data["explanation_json"]["selected_strategy"] == "SMART_RETRY"
    
    # Check that DECISION_EXPLAINED audit event is logged in db
    db = SessionLocal()
    try:
        audit_event = db.query(AuditLog).filter(
            AuditLog.case_id == "REC-DEMO-001",
            AuditLog.event_type == "DECISION_EXPLAINED"
        ).first()
        assert audit_event is not None
        assert audit_event.actor_name == "ExplainabilityService"
        assert "SMART_RETRY" in audit_event.decision_summary
        assert audit_event.metadata_json["selected_strategy"] == "SMART_RETRY"
    finally:
        db.close()

def test_batch_level_decision_insights():
    # Find a generated case from the DB where AI recommends normal recovery but policy will override due to high amount
    db = SessionLocal()
    disagreement_case_id = None
    try:
        all_cases = db.query(RecoveryCase).all()
        for c in all_cases:
            meta = c.metadata_json or {}
            category = meta.get("category")
            expected_strategy = meta.get("expected_strategy")
            # Category E cases have high transaction amount, which triggers HIGH_VALUE_TRANSACTION policy HITL rule
            if category == "E" and expected_strategy not in ["STOP_RECOVERY", "ESCALATE_TO_HUMAN"]:
                disagreement_case_id = c.case_id
                break
    finally:
        db.close()

    # Create batch with demo cases plus the disagreement case
    case_ids = ["REC-DEMO-002", "REC-DEMO-003", "REC-DEMO-004", "REC-DEMO-005"]
    if disagreement_case_id:
        case_ids.append(disagreement_case_id)

    create_res = client.post(
        "/api/batches",
        json={"batch_name": "Explainability Verification Batch", "case_ids": case_ids}
    )
    assert create_res.status_code == 200
    batch_id = create_res.json()["batch_id"]

    # Run the batch
    run_res = client.post(f"/api/batches/{batch_id}/run")
    assert run_res.status_code == 200
    
    # Get batch impact report
    impact_res = client.get(f"/api/batches/{batch_id}/impact")
    assert impact_res.status_code == 200
    impact_data = impact_res.json()
    
    # Verify decision insights
    insights = impact_data.get("decision_insights")
    assert insights is not None
    
    # There should be top STOP reasons (from REC-DEMO-004 which hits repeated failures)
    assert len(insights["top_stop_reasons"]) > 0
    assert any(r["reason"] in ["MAX_RETRIES_REACHED", "REPEATED_FAILURE"] for r in insights["top_stop_reasons"])
    
    # There should be top HITL reasons (from REC-DEMO-003 high value and REC-DEMO-005 customer dispute)
    assert len(insights["top_hitl_reasons"]) > 0
    hitl_rules = [r["reason"] for r in insights["top_hitl_reasons"]]
    assert "HIGH_VALUE_TRANSACTION" in hitl_rules
    assert "CUSTOMER_DISPUTE" in hitl_rules
    
    # There should be disagreement cases logged (REC-DEMO-003 recommendation SMART_RETRY or payment link is paused by policy)
    assert insights["total_disagreements"] > 0
    assert len(insights["disagreement_cases"]) > 0
    
    disagreement_case = insights["disagreement_cases"][0]
    assert "case_id" in disagreement_case
    assert disagreement_case["ai_recommendation"] is not None
    assert "policy engine" in disagreement_case["reason"].lower()
