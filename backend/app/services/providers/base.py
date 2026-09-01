from abc import ABC, abstractmethod
from typing import Dict, Any

class NormalizedExecutionResult:
    def __init__(
        self,
        execution_id: str,
        status: str,  # SUCCEEDED, FAILED, BLOCKED, CANCELLED
        provider_reference: str,
        recoverable: bool,
        message: str,
        recovered_amount: float = 0.0
    ):
        self.execution_id = execution_id
        self.status = status
        self.provider_reference = provider_reference
        self.recoverable = recoverable
        self.message = message
        self.recovered_amount = recovered_amount

class RecoveryProvider(ABC):
    @abstractmethod
    def execute_recovery_action(
        self,
        case_id: str,
        strategy: str,
        amount: float,
        attempt_number: int,
        execution_context: Dict[str, Any] = None
    ) -> NormalizedExecutionResult:
        """
        Executes a recovery action through the payment provider.
        """
        pass

    @abstractmethod
    def get_execution_status(self, execution_id: str) -> NormalizedExecutionResult:
        """
        Retrieves the status of a previously requested execution.
        """
        pass
