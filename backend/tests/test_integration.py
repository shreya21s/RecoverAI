import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    # Reset and seed database before each test
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_showcase_case_1_easy_recovery():
    # REC-DEMO-001 -> APPROVED -> EXECUTED (SUCCESS) -> RECOVERED
    response = client.post("/api/cases/REC-DEMO-001/process")
    assert response.status_code == 200
    data = response.json()
    
    # Check general properties
    assert data["case_id"] == "REC-DEMO-001"
    assert data["status"] == "RECOVERED"
    
    # Check policy result
    policy = data["policy"]
    assert policy["decision"] == "APPROVED"
    assert policy["action_allowed"] is True
    assert policy["requires_human_approval"] is False
    assert len(policy["triggered_rules"]) == 0
    
    # Check action execution result
    action_result = data["action_result"]
    assert action_result is not None
    assert action_result["action"] == "SMART_RETRY"
    assert action_result["result"] == "SUCCESS"
    assert action_result["recovered_amount"] == 4500.0

def test_showcase_case_2_payment_abandonment():
    # REC-DEMO-002 -> APPROVED -> EXECUTED (SUCCESS)
    response = client.post("/api/cases/REC-DEMO-002/process")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-002"
    
    policy = data["policy"]
    assert policy["decision"] == "APPROVED"
    assert policy["action_allowed"] is True
    assert policy["requires_human_approval"] is False
    
    action_result = data["action_result"]
    assert action_result is not None
    assert action_result["action"] == "SEND_PAYMENT_LINK"
    assert action_result["result"] == "SUCCESS"
    assert action_result["recovered_amount"] == 2500.0

def test_showcase_case_3_high_value_hitl():
    # REC-DEMO-003 -> HITL_REQUIRED -> NO EXECUTION (requires_human_approval=True)
    response = client.post("/api/cases/REC-DEMO-003/process")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-003"
    assert data["status"] == "WAITING_FOR_APPROVAL"
    
    policy = data["policy"]
    assert policy["decision"] == "HITL_REQUIRED"
    assert policy["action_allowed"] is False
    assert policy["requires_human_approval"] is True
    assert "HIGH_VALUE_TRANSACTION" in policy["triggered_rules"]
    assert "LOW_DIAGNOSIS_CONFIDENCE" in policy["triggered_rules"]
    
    assert data["action_result"] is None

def test_showcase_case_4_policy_stop():
    # REC-DEMO-004 -> BLOCKED (Max Retries) -> NO EXECUTION -> status STOPPED
    response = client.post("/api/cases/REC-DEMO-004/process")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-004"
    assert data["status"] == "STOPPED"
    
    policy = data["policy"]
    assert policy["decision"] in ["BLOCKED", "STOPPED"]
    assert policy["action_allowed"] is False
    assert policy["requires_human_approval"] is False
    assert any(rule in policy["triggered_rules"] for rule in ["MAX_RETRIES_REACHED", "REPEATED_FAILURE"])
    
    assert data["action_result"] is None

def test_showcase_case_5_customer_dispute():
    # REC-DEMO-005 -> HITL_REQUIRED (Customer Dispute) -> NO EXECUTION -> status ESCALATED
    response = client.post("/api/cases/REC-DEMO-005/process")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-005"
    assert data["status"] == "ESCALATED"
    
    policy = data["policy"]
    assert policy["decision"] == "HITL_REQUIRED"
    assert policy["action_allowed"] is False
    assert policy["requires_human_approval"] is True
    assert "CUSTOMER_DISPUTE" in policy["triggered_rules"]
    
    assert data["action_result"] is None
