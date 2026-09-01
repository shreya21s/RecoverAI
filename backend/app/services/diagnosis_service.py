from app.models.payment import Payment
from app.schemas.diagnosis import DiagnosisResult

class DiagnosisService:
    def diagnose_payment(self, payment: Payment) -> DiagnosisResult:
        """
        Determines the failure category and recommended recovery direction
        based on the payment status, failure codes, and dispute/retry flags.
        """
        evidence = []
        
        # Already Recovered check
        if payment.is_recovered:
            evidence.append("Payment record status indicates it is already recovered.")
            return DiagnosisResult(
                failure_category="ALREADY_RECOVERED",
                confidence=1.0,
                evidence=evidence,
                recommended_direction="STOP_RECOVERY"
            )
            
        # Dispute check
        if payment.is_disputed:
            evidence.append("Payment has been disputed by the customer.")
            return DiagnosisResult(
                failure_category="DISPUTED_PAYMENT",
                confidence=1.0,
                evidence=evidence,
                recommended_direction="ESCALATE_TO_HUMAN"
            )
            
        # Repeated Failure checks
        if payment.failure_code == "REPEATED_FAILURE" or payment.retry_count >= 3 or payment.reminder_count >= 3:
            evidence.append(f"Payment history indicates repeated unsuccessful attempts (Retries: {payment.retry_count}, Reminders: {payment.reminder_count}).")
            if payment.failure_code == "REPEATED_FAILURE":
                evidence.append("Failure code is explicitly marked as REPEATED_FAILURE.")
            return DiagnosisResult(
                failure_category="REPEATED_FAILURE",
                confidence=0.95,
                evidence=evidence,
                recommended_direction="STOP_RECOVERY"
            )
            
        # Temporary Failure check
        if payment.failure_code in ["TEMPORARY_BANK_FAILURE", "NETWORK_ERROR", "TEMPORARY_DECLINE"]:
            evidence.append(f"Failure code matches temporary category: {payment.failure_code}.")
            if payment.retry_count == 0:
                evidence.append("No previous retry attempts recorded.")
                confidence = 0.95
            else:
                evidence.append(f"Recorded retry attempts: {payment.retry_count}.")
                confidence = 0.88
            return DiagnosisResult(
                failure_category="TEMPORARY_FAILURE",
                confidence=confidence,
                evidence=evidence,
                recommended_direction="SMART_RETRY"
            )
            
        # Insufficient Funds check
        if payment.failure_code == "INSUFFICIENT_FUNDS":
            evidence.append("Failure code is INSUFFICIENT_FUNDS.")
            evidence.append(f"Retry attempts: {payment.retry_count}. Reminders: {payment.reminder_count}.")
            direction = "WAIT_AND_RETRY"
            if payment.retry_count >= 1:
                direction = "SEND_REMINDER"
            return DiagnosisResult(
                failure_category="INSUFFICIENT_FUNDS",
                confidence=0.90,
                evidence=evidence,
                recommended_direction=direction
            )
            
        # Payment Abandonment check
        if payment.failure_code == "PAYMENT_ABANDONED":
            evidence.append("Failure code indicates customer abandoned the checkout flow.")
            return DiagnosisResult(
                failure_category="PAYMENT_ABANDONMENT",
                confidence=0.92,
                evidence=evidence,
                recommended_direction="SEND_PAYMENT_LINK"
            )
            
        # Payment Method Issue check
        if payment.failure_code in ["EXPIRED_PAYMENT_METHOD", "INVALID_PAYMENT_METHOD", "AUTHENTICATION_FAILED"]:
            evidence.append(f"Failure code indicates payment method issue: {payment.failure_code}.")
            return DiagnosisResult(
                failure_category="PAYMENT_METHOD_ISSUE",
                confidence=0.88,
                evidence=evidence,
                recommended_direction="OFFER_ALTERNATIVE_PAYMENT_METHOD"
            )
            
        # Unknown Failure check
        evidence.append("Failure code does not map to any recognized failure scenario.")
        if payment.failure_code:
            evidence.append(f"Unrecognized failure code: {payment.failure_code}.")
        return DiagnosisResult(
            failure_category="UNKNOWN_FAILURE",
            confidence=0.60,
            evidence=evidence,
            recommended_direction="ESCALATE_TO_HUMAN"
        )
