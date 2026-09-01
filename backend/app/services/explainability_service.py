from typing import Dict, Any, List
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult
from app.schemas.strategy import StrategyResult
from app.config import settings

class ExplainabilityService:
    def generate_explanation(
        self,
        case: RecoveryCase,
        payment: Payment,
        customer: Customer,
        diagnosis: DiagnosisResult,
        customer_analysis: CustomerAnalysisResult,
        strategy: StrategyResult,
        policy_decision: str,  # "APPROVED" | "HITL_REQUIRED" | "STOPPED" | "BLOCKED"
        triggered_rules: List[str]
    ) -> Dict[str, Any]:
        # 1. Selected strategy
        selected_strategy = strategy.recommended_action
        
        # 2. Primary factors
        primary_factors = []
        
        # Factor A: Failure Category
        fail_impact = "neutral"
        if diagnosis.failure_category == "TEMPORARY_FAILURE":
            fail_impact = "positive"
            fail_explain = "Temporary bank or network failures are highly retriable and have a high probability of succeeding on retry."
        elif diagnosis.failure_category in ["REPEATED_FAILURE", "DISPUTED_PAYMENT", "ALREADY_RECOVERED"]:
            fail_impact = "negative"
            fail_explain = f"Failure category classified as {diagnosis.failure_category.replace('_', ' ')}, preventing further automatic recovery."
        elif diagnosis.failure_category == "INSUFFICIENT_FUNDS":
            fail_explain = "Insufficient funds means recovery requires waiting for customer deposits or sending reminders."
            fail_impact = "neutral" if customer_analysis.customer_quality_score > 0.40 else "negative"
        else:
            fail_explain = f"Failure due to {diagnosis.failure_category.replace('_', ' ')}. Rerouting or reminder required."
            fail_impact = "neutral"
        primary_factors.append({
            "factor": "Failure Category",
            "impact": fail_impact,
            "explanation": fail_explain
        })
        
        # Factor B: Customer Reliability & Quality
        quality = customer_analysis.customer_quality_score
        if quality > 0.75:
            q_impact = "positive"
            q_explain = f"Customer has a high quality score ({quality:.2f}), making them a highly reliable recovery target."
        elif quality > 0.40:
            q_impact = "neutral"
            q_explain = f"Customer has an average quality score ({quality:.2f})."
        else:
            q_impact = "negative"
            q_explain = f"Customer has a low quality score ({quality:.2f}), which increases the risk of recovery failure."
        primary_factors.append({
            "factor": "Customer Quality",
            "impact": q_impact,
            "explanation": q_explain
        })
        
        # Factor C: Transaction Amount
        amount = payment.amount
        if amount >= settings.HITL_AMOUNT_THRESHOLD:
            amt_impact = "negative"
            amt_explain = f"Transaction amount of Rs. {amount:,.2f} is high and exceeds the safety limit of Rs. {settings.HITL_AMOUNT_THRESHOLD:,.2f}."
        else:
            amt_impact = "positive"
            amt_explain = f"Transaction amount of Rs. {amount:,.2f} is within the threshold for automated recovery."
        primary_factors.append({
            "factor": "Transaction Amount",
            "impact": amt_impact,
            "explanation": amt_explain
        })

        # Factor D: Retries and Reminders
        retries = payment.retry_count
        if retries >= settings.MAX_RETRIES:
            retry_impact = "negative"
            retry_explain = f"Case has reached the maximum retry limit of {settings.MAX_RETRIES} attempts."
        elif retries > 0:
            retry_impact = "neutral"
            retry_explain = f"Case has already undergone {retries} retry attempts."
        else:
            retry_impact = "positive"
            retry_explain = "First retry attempt. No retry penalty applied."
        primary_factors.append({
            "factor": "Retry Attempts",
            "impact": retry_impact,
            "explanation": retry_explain
        })

        # Factor E: Recovery Probability
        prob = strategy.recovery_probability
        if prob >= settings.MIN_RECOVERY_PROBABILITY:
            prob_impact = "positive"
            prob_explain = f"Estimated recovery probability is {prob:.0%}, which is above the minimum threshold of {settings.MIN_RECOVERY_PROBABILITY:.0%}."
        else:
            prob_impact = "negative"
            prob_explain = f"Estimated recovery probability is {prob:.0%}, which is below the minimum safety threshold of {settings.MIN_RECOVERY_PROBABILITY:.0%}."
        primary_factors.append({
            "factor": "Recovery Probability",
            "impact": prob_impact,
            "explanation": prob_explain
        })

        # 3. Alternatives
        alternatives = []
        for alt in strategy.alternative_actions:
            reason_not = ""
            if selected_strategy == "SMART_RETRY" and alt == "WAIT_AND_RETRY":
                reason_not = "Customer quality score is high, so an immediate SMART RETRY is prioritized over a delayed retry."
            elif selected_strategy == "WAIT_AND_RETRY" and alt == "SMART_RETRY":
                reason_not = "Temporary failure or insufficient funds with average customer quality score suggests waiting for a retry window rather than retrying immediately."
            elif selected_strategy == "WAIT_AND_RETRY" and alt == "SEND_REMINDER":
                reason_not = "The customer's historical reliability warrants another automatic retry attempt before sending reminders."
            elif selected_strategy == "SEND_REMINDER" and alt == "WAIT_AND_RETRY":
                reason_not = "Customer quality/engagement is low, making automatic retries inefficient; direct reminder communication is preferred."
            elif selected_strategy == "SEND_PAYMENT_LINK" and alt == "SEND_REMINDER":
                reason_not = "Active customer engagement score suggests a direct payment link is more effective than a simple reminder message."
            elif selected_strategy == "OFFER_ALTERNATIVE_PAYMENT_METHOD" and alt == "SEND_PAYMENT_LINK":
                reason_not = "The failure is due to card method limitations (expired/invalid), so alternative payment methods are offered directly."
            elif selected_strategy == "ESCALATE_TO_HUMAN" and alt == "WAIT_AND_RETRY":
                reason_not = "The failure type is unknown or sensitive, requiring human operator triage before performing retries."
            else:
                reason_not = f"Prioritized {selected_strategy} over {alt} based on current risk-to-reward ratio."
            alternatives.append({
                "strategy": alt,
                "reason_not_selected": reason_not
            })

        # 4. Policy Explanation
        policy_explanation = {
            "decision": policy_decision,
            "triggered_rules": triggered_rules
        }

        # 5. Counterfactuals
        counterfactuals = []
        if policy_decision in ["STOPPED", "BLOCKED"]:
            if "MAX_RETRIES_REACHED" in triggered_rules:
                counterfactuals.append({
                    "condition": f"If retry attempts ({retries}) were less than {settings.MAX_RETRIES}",
                    "alternative_outcome": "The recommended strategy could have been evaluated for execution."
                })
            if "LOW_RECOVERY_PROBABILITY" in triggered_rules:
                counterfactuals.append({
                    "condition": f"If estimated recovery probability ({prob:.2f}) met or exceeded the threshold of {settings.MIN_RECOVERY_PROBABILITY:.2f}",
                    "alternative_outcome": "This case would not be blocked due to low probability."
                })
            if "ECONOMICALLY_NOT_VIABLE" in triggered_rules:
                counterfactuals.append({
                    "condition": "If expected recovery value exceeded Rs. 0.00 and action costs were lower",
                    "alternative_outcome": "The recovery action would satisfy economic viability checks."
                })
            if "REPEATED_FAILURE" in triggered_rules:
                counterfactuals.append({
                    "condition": "If the bank failure code did not indicate a repeated, consecutive failure state",
                    "alternative_outcome": "Recovery attempts would not be permanently halted."
                })
        elif policy_decision == "HITL_REQUIRED":
            if "HIGH_VALUE_TRANSACTION" in triggered_rules:
                counterfactuals.append({
                    "condition": f"If the transaction amount (Rs. {amount:,.2f}) were below the automatic execution safety threshold (Rs. {settings.HITL_AMOUNT_THRESHOLD:,.2f})",
                    "alternative_outcome": "The recovery action would run automatically without requiring manual review."
                })
            if "LOW_DIAGNOSIS_CONFIDENCE" in triggered_rules:
                counterfactuals.append({
                    "condition": f"If the diagnosis confidence ({diagnosis.confidence:.2f}) met or exceeded {settings.HITL_CONFIDENCE_THRESHOLD:.2f}",
                    "alternative_outcome": "The system would trust the AI categorization and run without review."
                })
            if "MULTIPLE_FAILED_ATTEMPTS" in triggered_rules:
                counterfactuals.append({
                    "condition": f"If total failed attempts ({retries + payment.reminder_count}) were less than {settings.HITL_FAILED_ATTEMPTS_THRESHOLD}",
                    "alternative_outcome": "The action would execute automatically before entering the escalation review loop."
                })
            if "CUSTOMER_DISPUTE" in triggered_rules:
                counterfactuals.append({
                    "condition": "If the customer did not have an active payment dispute",
                    "alternative_outcome": "The system could proceed with normal recovery processing instead of routing to risk review."
                })
        else: # APPROVED
            counterfactuals.append({
                "condition": f"If the retry attempts reached the maximum limit of {settings.MAX_RETRIES}",
                "alternative_outcome": "The policy decision would change to STOPPED."
            })
            counterfactuals.append({
                "condition": f"If the payment amount exceeded Rs. {settings.HITL_AMOUNT_THRESHOLD:,.2f}",
                "alternative_outcome": "The policy decision would change to HUMAN REVIEW REQUIRED."
            })

        # Override / Disagreement Analysis
        is_overridden = False
        override_reason = ""
        if selected_strategy not in ["STOP_RECOVERY", "ESCALATE_TO_HUMAN"] and policy_decision in ["STOPPED", "BLOCKED", "HITL_REQUIRED"]:
            is_overridden = True
            if policy_decision in ["STOPPED", "BLOCKED"]:
                override_reason = f"AI recommended recovery strategy ({selected_strategy}), but Policy Engine overrode it and STOPPED execution due to: {', '.join(triggered_rules)}."
            elif policy_decision == "HITL_REQUIRED":
                override_reason = f"AI recommended recovery strategy ({selected_strategy}), but Policy Engine paused execution for HUMAN REVIEW due to: {', '.join(triggered_rules)}."
            
        return {
            "selected_strategy": selected_strategy,
            "primary_factors": primary_factors,
            "alternatives": alternatives,
            "policy_explanation": policy_explanation,
            "counterfactuals": counterfactuals,
            "override_details": {
                "is_overridden": is_overridden,
                "override_reason": override_reason
            }
        }
