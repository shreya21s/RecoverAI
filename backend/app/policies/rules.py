from abc import ABC, abstractmethod
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult
from app.schemas.strategy import StrategyResult
from app.config import settings

class PolicyRule(ABC):
    @abstractmethod
    def evaluate(
        self,
        case: RecoveryCase,
        payment: Payment,
        customer: Customer,
        diagnosis: DiagnosisResult,
        customer_analysis: CustomerAnalysisResult,
        strategy: StrategyResult
    ) -> tuple[bool, str, str, bool, bool]:
        """
        Evaluates the rule against the provided context.
        Returns:
            (is_triggered, rule_name, reason, action_allowed, requires_human_approval)
        """
        pass

# --- TERMINAL RULES ---

class AlreadyRecoveredRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        if payment.is_recovered or payment.status == "RECOVERED":
            return (
                True,
                "ALREADY_RECOVERED",
                "Payment has already been recovered. No further recovery action is allowed.",
                False,
                False
            )
        return (False, "", "", True, False)

class TerminalCaseStatusRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        if case.status in ["RECOVERED", "STOPPED"]:
            return (
                True,
                "TERMINAL_CASE_STATUS",
                f"Case status is already in terminal state: {case.status}.",
                False,
                False
            )
        return (False, "", "", True, False)

# --- DISPUTE RULES ---

class CustomerDisputeRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        if payment.is_disputed:
            return (
                True,
                "CUSTOMER_DISPUTE",
                "Customer dispute detected. Automated recovery is suspended pending human review.",
                False,
                True
            )
        return (False, "", "", True, False)

# --- HARD STOPPING RULES ---

class RepeatedFailureRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        if diagnosis.failure_category == "REPEATED_FAILURE" or payment.failure_code == "REPEATED_FAILURE":
            return (
                True,
                "REPEATED_FAILURE",
                "Multiple attempts have failed consecutively. Recovery halted.",
                False,
                False
            )
        return (False, "", "", True, False)

class MaxRetriesRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        # Retry count threshold check (applies to retry actions)
        if strategy.recommended_action in ["SMART_RETRY", "WAIT_AND_RETRY"]:
            if payment.retry_count >= settings.MAX_RETRIES:
                return (
                    True,
                    "MAX_RETRIES_REACHED",
                    f"Payment has already reached the maximum retry limit of {settings.MAX_RETRIES}.",
                    False,
                    False
                )
        return (False, "", "", True, False)

class MaxRemindersRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        # Reminder count threshold check (applies to communication actions)
        if strategy.recommended_action in ["SEND_REMINDER", "SEND_PAYMENT_LINK", "OFFER_ALTERNATIVE_PAYMENT_METHOD"]:
            if payment.reminder_count >= settings.MAX_REMINDERS:
                return (
                    True,
                    "MAX_REMINDERS_REACHED",
                    f"Payment has already reached the maximum reminder limit of {settings.MAX_REMINDERS}.",
                    False,
                    False
                )
        return (False, "", "", True, False)

# --- ECONOMIC & PROBABILITY RULES ---

class LowRecoveryProbabilityRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        if strategy.recovery_probability < settings.MIN_RECOVERY_PROBABILITY:
            return (
                True,
                "LOW_RECOVERY_PROBABILITY",
                f"Estimated recovery probability ({strategy.recovery_probability:.2f}) is below the minimum threshold ({settings.MIN_RECOVERY_PROBABILITY:.2f}).",
                False,
                False
            )
        return (False, "", "", True, False)

class EconomicViabilityRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        if strategy.expected_recovery_value <= 0 or strategy.estimated_action_cost >= payment.amount:
            return (
                True,
                "ECONOMICALLY_NOT_VIABLE",
                "Estimated action costs exceed expected value, or transaction is economically non-viable.",
                False,
                False
            )
        return (False, "", "", True, False)

# --- HUMAN-IN-THE-LOOP RULES ---

class HighValueTransactionRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        if payment.amount >= settings.HITL_AMOUNT_THRESHOLD:
            return (
                True,
                "HIGH_VALUE_TRANSACTION",
                f"Payment amount (Rs. {payment.amount:,.2f}) exceeds the configured human review threshold (Rs. {settings.HITL_AMOUNT_THRESHOLD:,.2f}).",
                False,
                True
            )
        return (False, "", "", True, False)

class LowDiagnosisConfidenceRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        if diagnosis.confidence < settings.HITL_CONFIDENCE_THRESHOLD:
            return (
                True,
                "LOW_DIAGNOSIS_CONFIDENCE",
                f"Diagnosis confidence ({diagnosis.confidence:.2f}) is below the configured threshold ({settings.HITL_CONFIDENCE_THRESHOLD:.2f}).",
                False,
                True
            )
        return (False, "", "", True, False)

class MultipleFailedAttemptsRule(PolicyRule):
    def evaluate(self, case, payment, customer, diagnosis, customer_analysis, strategy):
        # Sum retries + reminders to check total failed attempts
        failed_attempts = payment.retry_count + payment.reminder_count
        if failed_attempts >= settings.HITL_FAILED_ATTEMPTS_THRESHOLD:
            return (
                True,
                "MULTIPLE_FAILED_ATTEMPTS",
                f"Total failed attempts ({failed_attempts}) meets or exceeds the human review threshold ({settings.HITL_FAILED_ATTEMPTS_THRESHOLD}).",
                False,
                True
            )
        return (False, "", "", True, False)
