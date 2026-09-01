from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult
from app.schemas.strategy import StrategyResult

class StrategyService:
    def determine_strategy(
        self,
        diagnosis: DiagnosisResult,
        customer_analysis: CustomerAnalysisResult,
        amount: float,
        retry_count: int,
        reminder_count: int
    ) -> StrategyResult:
        """
        Determines the optimal recovery strategy, action costs, and calculates
        expected recovery probability and expected recovery value.
        """
        recommended_action = "STOP_RECOVERY"
        alternative_actions = []
        reason = ""

        quality_score = customer_analysis.customer_quality_score
        engagement_score = customer_analysis.engagement_score
        failure_cat = diagnosis.failure_category

        # 1. Strategy Selection Rules
        if failure_cat == "TEMPORARY_FAILURE":
            if quality_score > 0.75:
                recommended_action = "SMART_RETRY"
                alternative_actions = ["WAIT_AND_RETRY"]
                reason = "Temporary network/bank failure for highly reliable customer. Recommended: automatic SMART_RETRY."
            elif quality_score > 0.40:
                recommended_action = "WAIT_AND_RETRY"
                alternative_actions = ["SMART_RETRY", "SEND_REMINDER"]
                reason = "Temporary failure for customer of average quality. Recommended: WAIT_AND_RETRY."
            else:
                recommended_action = "SEND_REMINDER"
                alternative_actions = ["WAIT_AND_RETRY"]
                reason = "Temporary failure for customer of lower quality. Recommended: SEND_REMINDER."

        elif failure_cat == "INSUFFICIENT_FUNDS":
            if quality_score > 0.75:
                recommended_action = "WAIT_AND_RETRY"
                alternative_actions = ["SMART_RETRY", "SEND_REMINDER"]
                reason = "Insufficient funds for reliable customer. Recommended: WAIT_AND_RETRY."
            elif quality_score > 0.40:
                recommended_action = "SEND_REMINDER"
                alternative_actions = ["WAIT_AND_RETRY"]
                reason = "Insufficient funds for average quality customer. Recommended: SEND_REMINDER."
            else:
                if retry_count >= 1:
                    recommended_action = "STOP_RECOVERY"
                    alternative_actions = []
                    reason = "Insufficient funds with low quality and previous failures. Recovery stopped."
                else:
                    recommended_action = "SEND_REMINDER"
                    alternative_actions = ["WAIT_AND_RETRY"]
                    reason = "Insufficient funds with low quality, first attempt. Recommended: SEND_REMINDER."

        elif failure_cat == "PAYMENT_ABANDONMENT":
            if engagement_score > 0.5:
                recommended_action = "SEND_PAYMENT_LINK"
                alternative_actions = ["SEND_REMINDER"]
                reason = "Checkout abandoned by an active, engaged customer. Recommended: SEND_PAYMENT_LINK."
            else:
                recommended_action = "SEND_REMINDER"
                alternative_actions = ["SEND_PAYMENT_LINK"]
                reason = "Checkout abandoned by low-engagement customer. Recommended: SEND_REMINDER."

        elif failure_cat == "PAYMENT_METHOD_ISSUE":
            recommended_action = "OFFER_ALTERNATIVE_PAYMENT_METHOD"
            alternative_actions = ["SEND_PAYMENT_LINK"]
            reason = "Failure due to method issues (expired/unauthorized). Recommended: OFFER_ALTERNATIVE_PAYMENT_METHOD."

        elif failure_cat == "UNKNOWN_FAILURE":
            recommended_action = "ESCALATE_TO_HUMAN"
            alternative_actions = ["WAIT_AND_RETRY"]
            reason = "Unknown failure trigger. Recommended: ESCALATE_TO_HUMAN."

        elif failure_cat == "REPEATED_FAILURE":
            recommended_action = "STOP_RECOVERY"
            alternative_actions = []
            reason = "Multiple attempts have failed consecutively. Recovery halted."

        elif failure_cat == "DISPUTED_PAYMENT":
            recommended_action = "ESCALATE_TO_HUMAN"
            alternative_actions = []
            reason = "Customer disputed the charge. Halted automated recovery and escalated."

        elif failure_cat == "ALREADY_RECOVERED":
            recommended_action = "STOP_RECOVERY"
            alternative_actions = []
            reason = "Payment already recovered successfully. Halted recovery."

        # 2. Probability Calculation
        base_probs = {
            "TEMPORARY_FAILURE": 0.85,
            "PAYMENT_ABANDONMENT": 0.70,
            "INSUFFICIENT_FUNDS": 0.50,
            "PAYMENT_METHOD_ISSUE": 0.60,
            "UNKNOWN_FAILURE": 0.30,
            "REPEATED_FAILURE": 0.05,
            "DISPUTED_PAYMENT": 0.02,
            "ALREADY_RECOVERED": 0.0
        }
        base_prob = base_probs.get(failure_cat, 0.40)

        # Adjust probability based on customer quality, engagement, and retry penalties
        quality_adj = quality_score * 0.15
        engagement_adj = engagement_score * 0.10
        retry_penalty = retry_count * 0.08
        reminder_penalty = reminder_count * 0.05

        prob = base_prob + quality_adj + engagement_adj - retry_penalty - reminder_penalty
        prob = max(0.0, min(1.0, prob))

        # Clamp overrides for terminal states
        if failure_cat in ["DISPUTED_PAYMENT", "ALREADY_RECOVERED", "REPEATED_FAILURE"] or recommended_action == "STOP_RECOVERY":
            prob = 0.0

        # 3. Cost & Expected Recovery Value
        costs = {
            "SMART_RETRY": 20.0,
            "WAIT_AND_RETRY": 10.0,
            "SEND_REMINDER": 5.0,
            "SEND_PAYMENT_LINK": 8.0,
            "OFFER_ALTERNATIVE_PAYMENT_METHOD": 15.0,
            "ESCALATE_TO_HUMAN": 100.0,
            "STOP_RECOVERY": 0.0
        }
        cost = costs.get(recommended_action, 10.0)
        expected_value = (amount * prob) - cost
        expected_value = max(0.0, expected_value)

        return StrategyResult(
            recommended_action=recommended_action,
            recovery_probability=prob,
            expected_recovery_value=expected_value,
            estimated_action_cost=cost,
            reason=reason,
            alternative_actions=alternative_actions
        )
