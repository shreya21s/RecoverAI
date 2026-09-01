from app.models.customer import Customer
from app.schemas.customer_analysis import CustomerAnalysisResult

class CustomerAnalysisService:
    def analyze_customer(self, customer: Customer) -> CustomerAnalysisResult:
        """
        Calculates explainable scores for customer payment reliability,
        engagement, and overall quality based on historical transactions.
        """
        evidence = []
        
        # Calculate reliability score
        total_payments = customer.total_successful_payments + customer.total_failed_payments
        if total_payments == 0:
            reliability = 0.5
            evidence.append("No transaction history available. Assumed default reliability score of 0.5.")
        else:
            reliability = customer.total_successful_payments / total_payments
            evidence.append(
                f"Customer transaction history: {customer.total_successful_payments} successful payments "
                f"out of {total_payments} total attempts ({reliability:.1%} success rate)."
            )

        # Normalize engagement score (stored 0-10 in generator)
        engagement = max(0.0, min(10.0, customer.engagement_score)) / 10.0
        evidence.append(f"Customer engagement score: {customer.engagement_score:.1f}/10 ({engagement:.1%}).")

        # Determine segment-based modifier
        segment_score = {
            "HIGH_VALUE_RELIABLE": 0.95,
            "RELIABLE": 0.80,
            "AVERAGE": 0.60,
            "AT_RISK": 0.35,
            "LOW_ENGAGEMENT": 0.15
        }.get(customer.segment, 0.5)
        evidence.append(f"Customer segment classification: {customer.segment} (weight: {segment_score:.2f}).")

        # Calculate overall quality score: reliability (40%), engagement (40%), segment weight (20%)
        quality_score = (reliability * 0.4) + (engagement * 0.4) + (segment_score * 0.2)
        quality_score = max(0.0, min(1.0, quality_score))
        evidence.append(f"Derived overall customer quality score: {quality_score:.2f}.")

        # Historical recovery probability: reliability (70%), engagement (30%)
        historical_recovery = (reliability * 0.7) + (engagement * 0.3)
        historical_recovery = max(0.0, min(1.0, historical_recovery))
        evidence.append(f"Calculated historical recovery probability: {historical_recovery:.2f}.")

        return CustomerAnalysisResult(
            customer_segment=customer.segment,
            customer_quality_score=quality_score,
            engagement_score=engagement,
            payment_reliability_score=reliability,
            historical_recovery_probability=historical_recovery,
            evidence=evidence
        )
