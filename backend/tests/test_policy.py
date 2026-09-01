import pytest
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult
from app.schemas.strategy import StrategyResult
from app.policies.policy_engine import PolicyEngine
from app.config import settings

@pytest.fixture
def policy_engine():
    return PolicyEngine()

@pytest.fixture
def base_context():
    customer = Customer(
        customer_id="CUST-TEST",
        name="Test Customer",
        segment="RELIABLE",
        lifetime_value=10000.0,
        total_successful_payments=10,
        total_failed_payments=1,
        average_payment_amount=1000.0,
        engagement_score=8.0
    )
    payment = Payment(
        payment_id="PAY-TEST",
        customer_id="CUST-TEST",
        amount=1000.0,
        currency="INR",
        payment_method="UPI",
        status="FAILED",
        failure_code="TEMPORARY_BANK_FAILURE",
        retry_count=0,
        reminder_count=0,
        is_disputed=False,
        is_recovered=False
    )
    case = RecoveryCase(
        case_id="REC-TEST",
        payment_id="PAY-TEST",
        status="PENDING",
        requires_human_approval=False
    )
    diagnosis = DiagnosisResult(
        failure_category="TEMPORARY_FAILURE",
        confidence=0.95,
        evidence=["Temporary test failure"],
        recommended_direction="SMART_RETRY"
    )
    analysis = CustomerAnalysisResult(
        customer_segment="RELIABLE",
        customer_quality_score=0.8,
        engagement_score=0.8,
        payment_reliability_score=0.9,
        historical_recovery_probability=0.85,
        evidence=["Customer is reliable"]
    )
    strategy = StrategyResult(
        recommended_action="SMART_RETRY",
        recovery_probability=0.85,
        expected_recovery_value=830.0,
        estimated_action_cost=20.0,
        reason="Test strategy recommendation",
        alternative_actions=["WAIT_AND_RETRY"]
    )
    return case, payment, customer, diagnosis, analysis, strategy

def test_normal_eligible_case_approved(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    
    assert result.decision == "APPROVED"
    assert result.action_allowed is True
    assert result.requires_human_approval is False
    assert len(result.triggered_rules) == 0

def test_already_recovered_payment_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    payment.is_recovered = True
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "ALREADY_RECOVERED" in result.triggered_rules
    assert "already been recovered" in result.reasons[0]

def test_already_recovered_status_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    payment.status = "RECOVERED"
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "ALREADY_RECOVERED" in result.triggered_rules

def test_terminal_case_status_recovered_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    case.status = "RECOVERED"
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "TERMINAL_CASE_STATUS" in result.triggered_rules

def test_terminal_case_status_stopped_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    case.status = "STOPPED"
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "TERMINAL_CASE_STATUS" in result.triggered_rules

def test_customer_dispute_requires_hitl(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    payment.is_disputed = True
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "HITL_REQUIRED"
    assert result.action_allowed is False
    assert result.requires_human_approval is True
    assert "CUSTOMER_DISPUTE" in result.triggered_rules
    assert "dispute" in result.reasons[0].lower()

def test_max_retries_reached_blocked(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    strategy.recommended_action = "SMART_RETRY"
    payment.retry_count = settings.MAX_RETRIES
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "BLOCKED"
    assert result.action_allowed is False
    assert "MAX_RETRIES_REACHED" in result.triggered_rules

def test_max_reminders_reached_blocked(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    strategy.recommended_action = "SEND_REMINDER"
    payment.reminder_count = settings.MAX_REMINDERS
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "BLOCKED"
    assert result.action_allowed is False
    assert "MAX_REMINDERS_REACHED" in result.triggered_rules

def test_repeated_failure_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    diagnosis.failure_category = "REPEATED_FAILURE"
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "REPEATED_FAILURE" in result.triggered_rules

def test_repeated_failure_code_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    payment.failure_code = "REPEATED_FAILURE"
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "REPEATED_FAILURE" in result.triggered_rules

def test_low_recovery_probability_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    strategy.recovery_probability = settings.MIN_RECOVERY_PROBABILITY - 0.01
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "LOW_RECOVERY_PROBABILITY" in result.triggered_rules

def test_economic_non_viable_value_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    strategy.expected_recovery_value = 0.0
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "ECONOMICALLY_NOT_VIABLE" in result.triggered_rules

def test_economic_non_viable_cost_stopped(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    strategy.estimated_action_cost = payment.amount + 10.0
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "STOPPED"
    assert result.action_allowed is False
    assert "ECONOMICALLY_NOT_VIABLE" in result.triggered_rules

def test_high_value_transaction_hitl(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    payment.amount = settings.HITL_AMOUNT_THRESHOLD
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "HITL_REQUIRED"
    assert result.action_allowed is False
    assert result.requires_human_approval is True
    assert "HIGH_VALUE_TRANSACTION" in result.triggered_rules

def test_low_diagnosis_confidence_hitl(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    diagnosis.confidence = settings.HITL_CONFIDENCE_THRESHOLD - 0.01
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "HITL_REQUIRED"
    assert result.action_allowed is False
    assert result.requires_human_approval is True
    assert "LOW_DIAGNOSIS_CONFIDENCE" in result.triggered_rules

def test_multiple_failed_attempts_hitl(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    payment.retry_count = 1
    payment.reminder_count = settings.HITL_FAILED_ATTEMPTS_THRESHOLD - 1
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "HITL_REQUIRED"
    assert result.action_allowed is False
    assert result.requires_human_approval is True
    assert "MULTIPLE_FAILED_ATTEMPTS" in result.triggered_rules

def test_combined_hitl_conditions(policy_engine, base_context):
    case, payment, customer, diagnosis, analysis, strategy = base_context
    payment.amount = settings.HITL_AMOUNT_THRESHOLD + 10000.0
    diagnosis.confidence = settings.HITL_CONFIDENCE_THRESHOLD - 0.05
    
    result = policy_engine.evaluate(case, payment, customer, diagnosis, analysis, strategy)
    assert result.decision == "HITL_REQUIRED"
    assert result.action_allowed is False
    assert result.requires_human_approval is True
    assert "HIGH_VALUE_TRANSACTION" in result.triggered_rules
    assert "LOW_DIAGNOSIS_CONFIDENCE" in result.triggered_rules
    assert len(result.triggered_rules) == 2
