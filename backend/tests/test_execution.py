import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.recovery_case import RecoveryCase, RecoveryCaseStatus
from app.models.payment import Payment
from app.models.recovery_action import RecoveryAction
from app.models.approval import HumanApproval, ApprovalDecision
from app.models.batch import RecoveryBatch, RecoveryBatchItem, BatchStatus
from app.services.recovery_execution_service import RecoveryExecutionService
from app.services.batch_service import BatchService
from app.services.metrics_service import MetricsService

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    response = client.post("/api/demo/reset")
    assert response.status_code == 200

# 1. Simulation execution success & 12. Attempt history is preserved
def test_simulation_execution_success_and_history():
    db = SessionLocal()
    try:
        # REC-DEMO-001 is seeded to succeed with SMART_RETRY
        execution_service = RecoveryExecutionService()
        action1 = execution_service.execute_recovery("REC-DEMO-001", "SMART_RETRY", db)
        
        # Verify attempt details
        assert action1.status == "SUCCEEDED"
        assert action1.attempt_number == 1
        assert action1.recovered_amount == 4500.0
        
        # Verify case and payment updated
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == "REC-DEMO-001").first()
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        assert case.status == "RECOVERED"
        assert payment.is_recovered is True
        assert payment.status == "RECOVERED"
        
        # Check action counts
        actions = db.query(RecoveryAction).filter(RecoveryAction.case_id == "REC-DEMO-001").all()
        assert len(actions) == 1
    finally:
        db.close()

# 2. Simulation execution failure & 10. Failed execution does not increase recovered revenue
def test_simulation_execution_failure_no_revenue():
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == "REC-DEMO-002").first()
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        
        # Force the simulation expected strategy to fail
        case.metadata_json = {
            "expected_strategy": "SMART_RETRY",
            "expected_outcome": "FAILED"
        }
        db.commit()
        
        execution_service = RecoveryExecutionService()
        action = execution_service.execute_recovery("REC-DEMO-002", "SMART_RETRY", db)
        
        assert action.status == "FAILED"
        assert action.recovered_amount == 0.0
        
        # Verify case remains processing/unrecovered
        db.refresh(case)
        db.refresh(payment)
        assert case.status == "PROCESSING"
        assert payment.is_recovered is False
        
        # Verify metrics shows 0 recovered revenue for this case
        metrics = MetricsService().calculate_metrics(db)
        # Verify revenue was not increased
        assert payment.payment_id not in [p.payment_id for p in db.query(Payment).filter(Payment.is_recovered == True).all()]
    finally:
        db.close()

# 3. Duplicate execution request & 4. Idempotency behavior
def test_duplicate_execution_idempotency():
    db = SessionLocal()
    try:
        execution_service = RecoveryExecutionService()
        
        # Trigger first execution
        action1 = execution_service.execute_recovery("REC-DEMO-001", "SMART_RETRY", db)
        db.refresh(action1)
        
        # Trigger duplicate request for same attempt
        action2 = execution_service.execute_recovery("REC-DEMO-001", "SMART_RETRY", db)
        
        # It should return the exact same action record
        assert action1.action_id == action2.action_id
        assert action2.status == "SUCCEEDED"
        
        # Verify only 1 action record exists in DB
        count = db.query(RecoveryAction).filter(RecoveryAction.case_id == "REC-DEMO-001").count()
        assert count == 1
    finally:
        db.close()

# 5. Terminal execution cannot run again
def test_terminal_execution_blocked():
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == "REC-DEMO-001").first()
        case.status = "RECOVERED"
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        payment.is_recovered = True
        db.commit()
        
        execution_service = RecoveryExecutionService()
        with pytest.raises(ValueError, match="Cannot execute recovery for case .* in terminal state"):
            execution_service.execute_recovery("REC-DEMO-001", "SMART_RETRY", db)
    finally:
        db.close()

# 6. Scheduled retry requires policy revalidation & 7. Policy blocks execution after state change
def test_scheduled_retry_revalidation_blocks():
    db = SessionLocal()
    try:
        # Seed a case in SCHEDULED status
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == "REC-DEMO-001").first()
        case.status = "SCHEDULED"
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        
        # Make a post-scheduling state change that violates rules:
        # e.g., customer disputes the payment
        payment.is_disputed = True
        db.commit()
        
        # Trigger scheduled retry directly via execution service (simulates retry worker)
        execution_service = RecoveryExecutionService()
        action = execution_service.execute_recovery("REC-DEMO-001", "SMART_RETRY", db)
        
        assert action.status == "BLOCKED"
        assert action.policy_decision == "HITL_REQUIRED"
        
        # Case should transition to human review since it requires approval
        db.refresh(case)
        assert case.status == "WAITING_FOR_APPROVAL"
    finally:
        db.close()

# 8. HITL approval still requires revalidation
def test_hitl_approval_revalidation():
    db = SessionLocal()
    try:
        # Seed case 3 in WAITING_FOR_APPROVAL
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == "REC-DEMO-003").first()
        case.status = "WAITING_FOR_APPROVAL"
        
        # Create approval record
        approval = HumanApproval(
            approval_id="APP-REC-DEMO-003-TEST",
            case_id="REC-DEMO-003",
            decision=ApprovalDecision.PENDING.value
        )
        db.add(approval)
        db.commit()
        
        # Let's change a database state to trigger a hard block during revalidation
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        payment.retry_count = 5 # exceeds retry limit of 3
        db.commit()
        
        # Attempt approval
        response = client.post("/api/approvals/REC-DEMO-003/approve", json={
            "reviewer_id": "test_reviewer",
            "reason": "Force approve retry"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # The revalidation should halt execution
        assert data["policy_revalidation"]["action_allowed"] is False
        assert data["final_status"] == "STOPPED"
        
        # Verify no successful attempt created
        action = db.query(RecoveryAction).filter(
            RecoveryAction.case_id == "REC-DEMO-003",
            RecoveryAction.status == "SUCCEEDED"
        ).first()
        assert action is None
    finally:
        db.close()

# 9. Recovered revenue is counted once
def test_recovered_revenue_counted_once():
    db = SessionLocal()
    try:
        # Verify initial metrics
        initial_metrics = MetricsService().calculate_metrics(db)
        
        # Execute case 1 (easy recovery success)
        execution_service = RecoveryExecutionService()
        action1 = execution_service.execute_recovery("REC-DEMO-001", "SMART_RETRY", db)
        assert action1.status == "SUCCEEDED"
        
        # Re-run same action or trigger idempotency
        action2 = execution_service.execute_recovery("REC-DEMO-001", "SMART_RETRY", db)
        assert action2.status == "SUCCEEDED"
        
        # Calculate metrics again
        updated_metrics = MetricsService().calculate_metrics(db)
        
        # Revenue should increase by exactly 4500.0 (the case amount) once
        assert updated_metrics["recovered_revenue"] == initial_metrics["recovered_revenue"] + 4500.0
    finally:
        db.close()

# 11. Batch processing isolates individual failures
def test_batch_processing_isolates_failures():
    db = SessionLocal()
    try:
        # Create a batch with some cases
        batch_service = BatchService()
        batch = batch_service.create_batch("Portfolio Failure Test", ["REC-DEMO-001", "REC-DEMO-002"], db)
        
        # Induce failure in REC-DEMO-001 by breaking its payment foreign key relation
        case1 = db.query(RecoveryCase).filter(RecoveryCase.case_id == "REC-DEMO-001").first()
        case1.payment_id = "NON-EXISTENT-ID"
        db.commit()
        
        # Run batch
        processed_batch = batch_service.process_batch(batch.batch_id, db)
        
        # Batch should complete with COMPLETED_WITH_ERRORS
        assert processed_batch.status == "COMPLETED_WITH_ERRORS"
        assert processed_batch.failed_cases == 1
        assert processed_batch.processed_cases == 1 # REC-DEMO-002 processed successfully
        
        # Verify REC-DEMO-002 batch item status is COMPLETED
        item2 = db.query(RecoveryBatchItem).filter(
            RecoveryBatchItem.batch_id == batch.batch_id,
            RecoveryBatchItem.case_id == "REC-DEMO-002"
        ).first()
        assert item2.processing_status == "COMPLETED"
        
        # Verify REC-DEMO-001 batch item status is FAILED
        item1 = db.query(RecoveryBatchItem).filter(
            RecoveryBatchItem.batch_id == batch.batch_id,
            RecoveryBatchItem.case_id == "REC-DEMO-001"
        ).first()
        assert item1.processing_status == "FAILED"
        assert "Payment not found" in item1.error_message or "NON-EXISTENT-ID" in item1.error_message
    finally:
        db.close()

# 13. Concurrent duplicate requests are safely handled
def test_concurrent_request_safety():
    db = SessionLocal()
    try:
        execution_service = RecoveryExecutionService()
        
        # Manually create an active attempt (PROCESSING)
        active_action = RecoveryAction(
            action_id="ACT-REC-DEMO-001-ACTIVE",
            case_id="REC-DEMO-001",
            action_type="SMART_RETRY",
            status="PROCESSING",
            attempt_number=1,
            requested_at=datetime.utcnow()
        )
        db.add(active_action)
        db.commit()
        
        # Execute concurrent request
        action = execution_service.execute_recovery("REC-DEMO-001", "SMART_RETRY", db)
        
        # Concurrency safety should return the active action instead of running a new execution
        assert action.action_id == "ACT-REC-DEMO-001-ACTIVE"
        assert action.status == "PROCESSING"
    finally:
        db.close()
