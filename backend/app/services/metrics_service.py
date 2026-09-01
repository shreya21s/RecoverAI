from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment

class MetricsService:
    def calculate_metrics(self, db: Session) -> dict:
        """
        Calculates live performance metrics of the recovery platform from database state.
        Includes total cases, state transitions, recovered/outstanding revenue, and recovery rate.
        """
        total_cases = db.query(RecoveryCase).count()
        recovered_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "RECOVERED").count()
        stopped_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "STOPPED").count()
        escalated_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "ESCALATED").count()

        # Recovered revenue: Sum of payment amount where is_recovered is True
        recovered_revenue = db.query(func.sum(Payment.amount)).filter(Payment.is_recovered == True).scalar() or 0.0

        # Outstanding revenue: Sum of payment amount where is_recovered is False
        outstanding_revenue = db.query(func.sum(Payment.amount)).filter(Payment.is_recovered == False).scalar() or 0.0

        # Total revenue is the sum of recovered + outstanding, representing the total initial failed revenue.
        # Eligible outstanding revenue is defined as all failed payments imported for recovery.
        total_revenue = recovered_revenue + outstanding_revenue

        # Recovery Rate: (Recovered Revenue / Eligible Outstanding Revenue) * 100
        recovery_rate = (recovered_revenue / total_revenue * 100) if total_revenue > 0 else 0.0

        return {
            "total_cases": total_cases,
            "recovered_cases": recovered_cases,
            "stopped_cases": stopped_cases,
            "escalated_cases": escalated_cases,
            "recovered_revenue": float(recovered_revenue),
            "outstanding_revenue": float(outstanding_revenue),
            "recovery_rate": float(round(recovery_rate, 2))
        }
