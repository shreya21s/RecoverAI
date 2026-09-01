import hashlib
from typing import Dict, Any
from app.services.providers.base import RecoveryProvider, NormalizedExecutionResult

class SimulatedRecoveryProvider(RecoveryProvider):
    def execute_recovery_action(
        self,
        case_id: str,
        strategy: str,
        amount: float,
        attempt_number: int,
        execution_context: Dict[str, Any] = None
    ) -> NormalizedExecutionResult:
        """
        Executes a simulated recovery action deterministically.
        Supports expected seed outcomes and stable hash-based fallbacks.
        """
        meta = execution_context or {}
        exec_id = f"EXE-SIM-{case_id}-{attempt_number}"
        ref_id = f"REF-SIM-{hashlib.md5(exec_id.encode()).hexdigest()[:6].upper()}"

        # 1. Seed-based deterministic outcomes
        if "expected_strategy" in meta and "expected_outcome" in meta:
            if meta["expected_strategy"] == strategy:
                expected_outcome = meta["expected_outcome"]
                
                if expected_outcome == "SUCCESS":
                    return NormalizedExecutionResult(
                        execution_id=exec_id,
                        status="SUCCEEDED",
                        provider_reference=ref_id,
                        recoverable=True,
                        message="Simulated transaction completed successfully",
                        recovered_amount=meta.get("recovered_amount", amount)
                    )
                elif expected_outcome == "FAILED":
                    return NormalizedExecutionResult(
                        execution_id=exec_id,
                        status="FAILED",
                        provider_reference=ref_id,
                        recoverable=True,
                        message="Simulated transaction declined by customer bank",
                        recovered_amount=0.0
                    )
                elif expected_outcome == "NO_RESPONSE":
                    return NormalizedExecutionResult(
                        execution_id=exec_id,
                        status="FAILED",
                        provider_reference=ref_id,
                        recoverable=True,
                        message="Simulated customer contact attempt timed out",
                        recovered_amount=0.0
                    )
                elif expected_outcome == "STOPPED_BY_POLICY":
                    return NormalizedExecutionResult(
                        execution_id=exec_id,
                        status="BLOCKED",
                        provider_reference=ref_id,
                        recoverable=False,
                        message="Simulated policy stop prevents execution",
                        recovered_amount=0.0
                    )
                elif expected_outcome == "REQUIRES_APPROVAL":
                    return NormalizedExecutionResult(
                        execution_id=exec_id,
                        status="BLOCKED",
                        provider_reference=ref_id,
                        recoverable=False,
                        message="Simulated human-in-the-loop review required",
                        recovered_amount=0.0
                    )

        # 2. Hash-based deterministic fallback (stable, reproducible output)
        hash_input = f"{case_id}:{strategy}:{attempt_number}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        modulo = hash_val % 100
        
        prob = meta.get("recovery_probability", 0.5)
        threshold = int(prob * 100)

        if strategy == "STOP_RECOVERY":
            return NormalizedExecutionResult(
                execution_id=exec_id,
                status="BLOCKED",
                provider_reference=ref_id,
                recoverable=False,
                message="Recovery terminated by policy engine",
                recovered_amount=0.0
            )
        elif strategy == "ESCALATE_TO_HUMAN":
            return NormalizedExecutionResult(
                execution_id=exec_id,
                status="SUCCEEDED",
                provider_reference=ref_id,
                recoverable=False,
                message="Case escalated to manual operations review queue",
                recovered_amount=0.0
            )
        elif modulo < threshold:
            return NormalizedExecutionResult(
                execution_id=exec_id,
                status="SUCCEEDED",
                provider_reference=ref_id,
                recoverable=True,
                message="Transaction approved and settled (simulated)",
                recovered_amount=amount
            )
        elif modulo < threshold + 15:
            # Temporary/retryable simulated decline
            return NormalizedExecutionResult(
                execution_id=exec_id,
                status="FAILED",
                provider_reference=ref_id,
                recoverable=True,
                message="Temporary network timeout at simulated gateway",
                recovered_amount=0.0
            )
        else:
            # Permanent simulated decline
            return NormalizedExecutionResult(
                execution_id=exec_id,
                status="FAILED",
                provider_reference=ref_id,
                recoverable=True,
                message="Simulated card balance insufficient",
                recovered_amount=0.0
            )

    def get_execution_status(self, execution_id: str) -> NormalizedExecutionResult:
        """
        Mock lookup returning complete.
        """
        return NormalizedExecutionResult(
            execution_id=execution_id,
            status="SUCCEEDED",
            provider_reference="REF-SIM-GET",
            recoverable=True,
            message="Checked simulated status: completed synchronously"
        )
