import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.batch import RecoveryBatch, RecoveryBatchItem, BatchStatus
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.audit_log import AuditLog
from app.db.database import SessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    response = client.post("/api/demo/reset")
    assert response.status_code == 200

def test_batch_creation_validation():
    # 1. Try to create batch with terminal case
    # Let's run REC-DEMO-001 (easy recovery) first to make it terminal/RECOVERED
    client.post("/api/cases/REC-DEMO-001/run")
    
    # Try to create batch explicitly including REC-DEMO-001
    create_res = client.post(
        "/api/batches",
        json={"batch_name": "Terminal Case Batch", "case_ids": ["REC-DEMO-001", "REC-DEMO-002"]}
    )
    assert create_res.status_code == 400
    assert "ineligible" in create_res.json()["detail"]

    # 2. Try to create batch with non-existent case ID
    create_res_invalid = client.post(
        "/api/batches",
        json={"batch_name": "Invalid ID Batch", "case_ids": ["INVALID-CASE-ID"]}
    )
    assert create_res_invalid.status_code == 400
    assert "not found" in create_res_invalid.json()["detail"].lower()

    # 3. Create batch automatically (without passing case_ids)
    # It should pick up all eligible cases (excluding REC-DEMO-001 which is already recovered)
    create_res_auto = client.post(
        "/api/batches",
        json={"batch_name": "Automatic Selection Batch"}
    )
    assert create_res_auto.status_code == 200
    auto_data = create_res_auto.json()
    assert auto_data["total_cases"] > 0
    assert not any(c["case_id"] == "REC-DEMO-001" for c in auto_data["cases"])

def test_batch_execution_metrics_and_audit():
    # Create batch containing the remaining demo cases
    case_ids = ["REC-DEMO-002", "REC-DEMO-003", "REC-DEMO-004", "REC-DEMO-005"]
    create_res = client.post(
        "/api/batches",
        json={"batch_name": "Verification Batch", "case_ids": case_ids}
    )
    assert create_res.status_code == 200
    batch_data = create_res.json()
    batch_id = batch_data["batch_id"]

    # Run the batch
    run_res = client.post(f"/api/batches/{batch_id}/run")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] == BatchStatus.COMPLETED.value
    assert run_data["processed_cases"] == 4
    
    # Check that individual case processing outcome matches policy engine findings:
    # - REC-DEMO-002 (payment abandonment) -> APPROVED -> executed
    # - REC-DEMO-003 (high value HITL) -> HITL_REQUIRED -> WAITING_FOR_APPROVAL
    # - REC-DEMO-004 (repeated failure) -> STOPPED -> STOPPED
    # - REC-DEMO-005 (customer dispute) -> BLOCKED -> ESCALATED/STOPPED/BLOCKED
    
    # Verify cases list outputs final status
    cases_map = {c["case_id"]: c for c in run_data["cases"]}
    assert cases_map["REC-DEMO-002"]["final_status"] == "RECOVERED"
    assert cases_map["REC-DEMO-003"]["final_status"] == "WAITING_FOR_APPROVAL"
    assert cases_map["REC-DEMO-004"]["final_status"] == "STOPPED"
    
    # Verify GET /api/batches/{batch_id}/impact report returns valid metrics
    impact_res = client.get(f"/api/batches/{batch_id}/impact")
    assert impact_res.status_code == 200
    impact_data = impact_res.json()
    
    # Check metrics values:
    # Outstanding amount is the sum of payments
    # Recovered amount is from REC-DEMO-002 (amount 15000)
    assert impact_data["financial_impact"]["recovered_revenue"] == 2500.0
    assert impact_data["financial_impact"]["unrecovered_revenue"] > 0.0
    assert impact_data["financial_impact"]["recovery_rate"] > 0.0
    
    # Baseline comparison metrics
    assert "baseline_recovered_revenue" in impact_data["baseline_comparison"]
    assert "incremental_revenue" in impact_data["baseline_comparison"]
    
    # Verify GET /api/audit/batches/{batch_id} returns chronological events
    audit_res = client.get(f"/api/audit/batches/{batch_id}")
    assert audit_res.status_code == 200
    audit_events = audit_res.json()
    assert len(audit_events) > 0
    
    # Check chronological ordering: timestamp values are increasing
    timestamps = [e["timestamp"] for e in audit_events]
    assert sorted(timestamps) == timestamps
    
    # Check that we logged the CASE_PROCESSING_STARTED and CASE_COMPLETED events
    event_types = [e["event_type"] for e in audit_events]
    assert "CASE_PROCESSING_STARTED" in event_types
    assert "CASE_COMPLETED" in event_types

    # Idempotency check: running again should yield 400 Bad Request
    run_dup = client.post(f"/api/batches/{batch_id}/run")
    assert run_dup.status_code == 400

def test_batch_error_isolation():
    # Create batch
    case_ids = ["REC-DEMO-002", "REC-DEMO-003"]
    create_res = client.post(
        "/api/batches",
        json={"batch_name": "Error Isolation Batch", "case_ids": case_ids}
    )
    assert create_res.status_code == 200
    batch_id = create_res.json()["batch_id"]

    # Mock run_recovery_graph on REC-DEMO-002 to throw a technical exception
    # It should fail REC-DEMO-002 but complete batch execution successfully
    def mock_run(case_id, db, human_decision=None, batch_id=None):
        if case_id == "REC-DEMO-002":
            raise ValueError("Technical simulation database deadlock.")
        # Default behavior
        from app.graphs.recovery_graph import run_recovery_graph
        # Un-patched invocation
        with patch("app.services.batch_service.run_recovery_graph", side_effect=None):
            return run_recovery_graph(case_id, db, human_decision=human_decision, batch_id=batch_id)

    with patch("app.services.batch_service.run_recovery_graph", side_effect=mock_run):
        run_res = client.post(f"/api/batches/{batch_id}/run")
        assert run_res.status_code == 200
        run_data = run_res.json()
        
        # Status should be COMPLETED_WITH_ERRORS
        assert run_data["status"] == BatchStatus.COMPLETED_WITH_ERRORS.value
        assert run_data["failed_cases"] == 1
        assert run_data["processed_cases"] == 1 # 1 succeeded, 1 failed technical
        
        # Verify cases list error messages
        cases_map = {c["case_id"]: c for c in run_data["cases"]}
        assert cases_map["REC-DEMO-002"]["processing_status"] == "FAILED"
        assert "deadlock" in cases_map["REC-DEMO-002"]["error_message"]
        
        assert cases_map["REC-DEMO-003"]["processing_status"] == "COMPLETED"
        assert cases_map["REC-DEMO-003"]["final_status"] == "WAITING_FOR_APPROVAL"
