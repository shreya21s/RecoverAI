import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.audit_log import AuditLog

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    response = client.post("/api/demo/reset")
    assert response.status_code == 200

def test_create_custom_case_and_run():
    payload = {
        "amount": 65000.0,
        "currency": "INR",
        "payment_method": "UPI",
        "failure_code": "TEMPORARY_BANK_FAILURE",
        "retry_count": 0,
        "reminder_count": 0,
        "is_disputed": False,
        "customer_name": "Rohan Deshmukh",
        "customer_segment": "HIGH_VALUE_RELIABLE",
        "customer_ltv": 200000.0,
        "successful_payments": 20,
        "failed_payments": 1,
        "engagement_score": 9.2,
        "auto_run": True
    }
    
    response = client.post("/api/cases", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["amount"] == 65000.0
    assert data["case_id"].startswith("REC-USER-")
    assert data["graph_result"] is not None
    assert data["graph_result"]["workflow_status"] == "completed"
    
    # Verify in DB
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == data["case_id"]).first()
        assert case is not None
        payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
        assert payment.amount == 65000.0
        customer = db.query(Customer).filter(Customer.customer_id == payment.customer_id).first()
        assert customer.name == "Rohan Deshmukh"
        
        # Verify audit log was created
        audit = db.query(AuditLog).filter(AuditLog.case_id == data["case_id"]).first()
        assert audit is not None
    finally:
        db.close()

def test_create_custom_case_high_value_hitl():
    payload = {
        "amount": 95000.0,
        "currency": "INR",
        "payment_method": "NETBANKING",
        "failure_code": "UNKNOWN_FAILURE",
        "retry_count": 1,
        "reminder_count": 1,
        "is_disputed": False,
        "customer_name": "VIP Enterprise Client",
        "customer_segment": "AT_RISK",
        "customer_ltv": 95000.0,
        "successful_payments": 2,
        "failed_payments": 3,
        "engagement_score": 4.0,
        "auto_run": True
    }
    
    response = client.post("/api/cases", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["graph_result"]["policy"]["decision"] == "HITL_REQUIRED"
    assert "HIGH_VALUE_TRANSACTION" in data["graph_result"]["policy"]["triggered_rules"]
    assert data["graph_result"]["final_status"] == "WAITING_FOR_APPROVAL"
