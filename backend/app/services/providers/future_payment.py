from typing import Dict, Any
from app.services.providers.base import RecoveryProvider, NormalizedExecutionResult

class FuturePaymentProviderAdapter(RecoveryProvider):
    """
    Integration-ready placeholder for a future payment network (e.g. Razorpay, Stripe).
    Demonstrates isolation: core logic doesn't need to change when replacing simulation.
    """
    def execute_recovery_action(
        self,
        case_id: str,
        strategy: str,
        amount: float,
        attempt_number: int,
        execution_context: Dict[str, Any] = None
    ) -> NormalizedExecutionResult:
        raise NotImplementedError(
            "FuturePaymentProviderAdapter is a structural integration placeholder. "
            "Please run with config SIMULATION_MODE=true to use the SimulatedRecoveryProvider."
        )

    def get_execution_status(self, execution_id: str) -> NormalizedExecutionResult:
        raise NotImplementedError(
            "FuturePaymentProviderAdapter is a structural integration placeholder. "
            "Please run with config SIMULATION_MODE=true to use the SimulatedRecoveryProvider."
        )
