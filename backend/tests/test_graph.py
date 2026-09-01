import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_graph_showcase_case_1_easy_recovery():
    # REC-DEMO-001 -> APPROVED -> EXECUTED (SUCCESS) -> RECOVERED
    response = client.post("/api/cases/REC-DEMO-001/run")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-001"
    assert data["workflow_status"] == "completed"
    assert data["final_status"] == "RECOVERED"
    
    policy = data["policy"]
    assert policy["decision"] == "APPROVED"
    assert policy["action_allowed"] is True
    
    action_result = data["action_result"]
    assert action_result is not None
    assert action_result["action"] == "SMART_RETRY"
    assert action_result["result"] == "SUCCESS"
    assert action_result["recovered_amount"] == 4500.0
    
    trace_steps = [t["step"] for t in data["agent_trace"]]
    assert "load_case" in trace_steps
    assert "supervisor" in trace_steps
    assert "diagnosis_agent" in trace_steps
    assert "customer_agent" in trace_steps
    assert "strategy_agent" in trace_steps
    assert "policy_engine" in trace_steps
    assert "execution_node" in trace_steps
    assert "finalize" in trace_steps

def test_graph_showcase_case_2_payment_abandonment():
    # REC-DEMO-002 -> APPROVED -> EXECUTED (SUCCESS)
    response = client.post("/api/cases/REC-DEMO-002/run")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-002"
    assert data["workflow_status"] == "completed"
    
    policy = data["policy"]
    assert policy["decision"] == "APPROVED"
    
    action_result = data["action_result"]
    assert action_result is not None
    assert action_result["action"] == "SEND_PAYMENT_LINK"
    assert action_result["result"] == "SUCCESS"
    assert action_result["recovered_amount"] == 2500.0

def test_graph_showcase_case_3_high_value_hitl():
    # REC-DEMO-003 -> HITL_REQUIRED -> NO EXECUTION (requires_human_approval=True)
    response = client.post("/api/cases/REC-DEMO-003/run")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-003"
    assert data["final_status"] == "WAITING_FOR_APPROVAL"
    assert data["action_result"] is None
    
    policy = data["policy"]
    assert policy["decision"] == "HITL_REQUIRED"
    assert policy["action_allowed"] is False
    assert policy["requires_human_approval"] is True
    assert "HIGH_VALUE_TRANSACTION" in policy["triggered_rules"]
    assert "LOW_DIAGNOSIS_CONFIDENCE" in policy["triggered_rules"]
    
    trace_steps = [t["step"] for t in data["agent_trace"]]
    assert "hitl_pending" in trace_steps

def test_graph_showcase_case_4_policy_stop():
    # REC-DEMO-004 -> BLOCKED or STOPPED -> NO EXECUTION -> status STOPPED
    response = client.post("/api/cases/REC-DEMO-004/run")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-004"
    assert data["final_status"] == "STOPPED"
    assert data["action_result"] is None
    
    policy = data["policy"]
    assert policy["decision"] in ["BLOCKED", "STOPPED"]
    assert policy["action_allowed"] is False
    assert any(rule in policy["triggered_rules"] for rule in ["MAX_RETRIES_REACHED", "REPEATED_FAILURE"])

def test_graph_showcase_case_5_customer_dispute():
    # REC-DEMO-005 -> HITL_REQUIRED (Customer Dispute) -> NO EXECUTION -> status ESCALATED
    response = client.post("/api/cases/REC-DEMO-005/run")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "REC-DEMO-005"
    assert data["final_status"] == "ESCALATED"
    assert data["action_result"] is None
    
    policy = data["policy"]
    assert policy["decision"] == "HITL_REQUIRED"
    assert policy["action_allowed"] is False
    assert policy["requires_human_approval"] is True
    assert "CUSTOMER_DISPUTE" in policy["triggered_rules"]
