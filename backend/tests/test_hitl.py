import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.approval import HumanApproval, ApprovalDecision
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.recovery_action import RecoveryAction
from app.db.database import SessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_hitl_lifecycle_rejection():
    # 1. Run REC-DEMO-003 through graph to trigger HITL_REQUIRED
    run_response = client.post("/api/cases/REC-DEMO-003/run")
    assert run_response.status_code == 200
    run_data = run_response.json()
    assert run_data["final_status"] == "WAITING_FOR_APPROVAL"
    assert run_data["policy"]["decision"] == "HITL_REQUIRED"
    assert run_data["action_result"] is None
    
    # Verify approval record exists in PENDING state
    db = SessionLocal()
    try:
        app_record = db.query(HumanApproval).filter(HumanApproval.case_id == "REC-DEMO-003").first()
        assert app_record is not None
        assert app_record.decision == ApprovalDecision.PENDING.value
    finally:
        db.close()
        
    # 2. Verify GET /api/approvals/pending returns the case
    pending_res = client.get("/api/approvals/pending")
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert len(pending_list) >= 1
    assert any(x["case_id"] == "REC-DEMO-003" for x in pending_list)
    
    # 3. Verify GET /api/approvals/{case_id} returns review context
    context_res = client.get("/api/approvals/REC-DEMO-003")
    assert context_res.status_code == 200
    context_data = context_res.json()
    assert context_data["case_id"] == "REC-DEMO-003"
    assert context_data["payment"]["amount"] == 75000.0
    assert "HIGH_VALUE_TRANSACTION" in context_data["policy"]["triggered_rules"]

    # 4. Human Rejects the case
    reject_res = client.post(
        "/api/approvals/REC-DEMO-003/reject",
        json={"reviewer_id": "test_reviewer", "reason": "Too high risk for auto retry"}
    )
    assert reject_res.status_code == 200
    reject_data = reject_res.json()
    assert reject_data["human_decision"]["decision"] == "REJECTED"
    assert reject_data["final_status"] == "STOPPED"
    assert reject_data["action_result"] is None
    
    # Verify DB state
    db = SessionLocal()
    try:
        app_record = db.query(HumanApproval).filter(HumanApproval.case_id == "REC-DEMO-003").first()
        assert app_record.decision == ApprovalDecision.REJECTED.value
        assert app_record.reviewer == "test_reviewer"
        
        # Verify no recovery action was executed
        actions = db.query(RecoveryAction).filter(RecoveryAction.case_id == "REC-DEMO-003").all()
        assert len(actions) == 0
        
        # Verify RecoveryCase is STOPPED
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == "REC-DEMO-003").first()
        assert case.status == "STOPPED"
    finally:
        db.close()

    # 5. Rejecting again should yield 400 Bad Request
    reject_dup = client.post(
        "/api/approvals/REC-DEMO-003/reject",
        json={"reviewer_id": "test_reviewer", "reason": "Already rejected"}
    )
    assert reject_dup.status_code == 400

    # 6. Approving after rejection should yield 400 Bad Request
    approve_dup = client.post(
        "/api/approvals/REC-DEMO-003/approve",
        json={"reviewer_id": "test_reviewer", "reason": "Approve after reject"}
    )
    assert approve_dup.status_code == 400


def test_hitl_lifecycle_approval():
    # 1. Trigger initial HITL run
    client.post("/api/cases/REC-DEMO-003/run")
    
    # 2. Human Approves the case
    approve_res = client.post(
        "/api/approvals/REC-DEMO-003/approve",
        json={"reviewer_id": "admin_reviewer", "reason": "Controlled override permitted"}
    )
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    
    assert approve_data["human_decision"]["decision"] == "APPROVED"
    # Policy revalidation overrides soft rules so it is APPROVED
    assert approve_data["policy_revalidation"]["decision"] == "APPROVED"
    assert approve_data["policy_revalidation"]["action_allowed"] is True
    
    # Action result of ESCALATE_TO_HUMAN is ESCALATED status
    assert approve_data["final_status"] == "ESCALATED"
    assert approve_data["action_result"] is not None
    assert approve_data["action_result"]["action"] == "ESCALATE_TO_HUMAN"
    
    db = SessionLocal()
    try:
        # Verify approval is RESOLVED
        app_record = db.query(HumanApproval).filter(HumanApproval.case_id == "REC-DEMO-003").first()
        assert app_record.decision == ApprovalDecision.APPROVED.value
        
        # Verify exactly 1 recovery action was executed
        actions = db.query(RecoveryAction).filter(RecoveryAction.case_id == "REC-DEMO-003").all()
        assert len(actions) == 1
    finally:
        db.close()

    # 3. Approving again should yield 400 Bad Request
    approve_dup = client.post(
        "/api/approvals/REC-DEMO-003/approve",
        json={"reviewer_id": "admin_reviewer", "reason": "Approve again"}
    )
    assert approve_dup.status_code == 400


def test_hard_stopping_rule_cannot_be_overridden():
    # REC-DEMO-004 is a repeated failure (hard stop).
    # Trigger initial run to make sure database starts at STOPPED
    client.post("/api/cases/REC-DEMO-004/run")
    
    # Try to execute by explicitly running graph with approved decision
    # (Since there is no pending approval for a hard stopped case, hitl_service approve_case will block it.
    # We will test running recovery graph with human_decision approved directly)
    db = SessionLocal()
    try:
        from app.graphs.recovery_graph import run_recovery_graph
        # Invoke graph directly with APPROVED human decision
        result_state = run_recovery_graph(
            "REC-DEMO-004", db, 
            human_decision={"decision": "APPROVED", "reviewer_id": "admin", "reason": "Try to force"}
        )
        
        # Revalidation should fail due to hard stopping rule and NOT allow action execution
        assert result_state["policy"]["decision"] == "STOPPED"
        assert result_state["policy"]["action_allowed"] is False
        assert any(r in result_state["policy"]["triggered_rules"] for r in ["REPEATED_FAILURE", "TERMINAL_CASE_STATUS"])
        assert result_state["action_result"] is None
        assert result_state["final_status"] == "STOPPED"
    finally:
        db.close()


def test_approve_already_recovered_case():
    # Seed the case as already recovered (REC-DEMO-001 initially pending, but let's run it first to make it RECOVERED)
    client.post("/api/cases/REC-DEMO-001/run")
    
    # Attempting to approve it should yield 400 Bad Request since there is no pending request
    # and case is in terminal state
    approve_res = client.post(
        "/api/approvals/REC-DEMO-001/approve",
        json={"reviewer_id": "admin", "reason": "Try to approve recovered case"}
    )
    assert approve_res.status_code == 400
