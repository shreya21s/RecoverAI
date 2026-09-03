import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_policy_config():
    response = client.get("/api/policy/config")
    assert response.status_code == 200
    data = response.json()
    assert "MAX_RETRIES" in data
    assert "HITL_AMOUNT_THRESHOLD" in data
    assert "MIN_RECOVERY_PROBABILITY" in data

def test_update_and_reset_policy_config():
    # Update threshold to 75,000
    update_res = client.put("/api/policy/config", json={
        "HITL_AMOUNT_THRESHOLD": 75000.0,
        "MAX_RETRIES": 4
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["HITL_AMOUNT_THRESHOLD"] == 75000.0
    assert updated_data["MAX_RETRIES"] == 4

    # Reset
    reset_res = client.post("/api/policy/reset")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["HITL_AMOUNT_THRESHOLD"] == 50000.0
    assert reset_data["MAX_RETRIES"] == 3
