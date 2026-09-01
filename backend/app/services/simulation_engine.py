import hashlib
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.schemas.recovery_result import ActionResultSchema

class SimulationEngine:
    def execute_simulation(self, case: RecoveryCase, recommended_action: str, payment: Payment) -> ActionResultSchema:
        """
        Executes a simulated recovery action deterministically. Looks up the expected
        outcome mapping defined during seeding first, and falls back to a stable,
        hash-based calculation otherwise.
        """
        meta = case.metadata_json or {}
        
        # Check if seeder-defined mapping matches the executed action
        if "expected_strategy" in meta and "expected_outcome" in meta:
            if meta["expected_strategy"] == recommended_action:
                expected_outcome = meta["expected_outcome"]
                
                # Map expected outcome string to standard simulation result states
                if expected_outcome == "SUCCESS":
                    result = "SUCCESS"
                    recovered_amount = meta.get("recovered_amount", payment.amount)
                elif expected_outcome == "FAILED":
                    result = "FAILED"
                    recovered_amount = 0.0
                elif expected_outcome == "NO_RESPONSE":
                    result = "NO_RESPONSE"
                    recovered_amount = 0.0
                elif expected_outcome == "STOPPED_BY_POLICY":
                    result = "STOPPED"
                    recovered_amount = 0.0
                elif expected_outcome == "REQUIRES_APPROVAL":
                    result = "ESCALATED"
                    recovered_amount = 0.0
                else:
                    result = expected_outcome
                    recovered_amount = meta.get("recovered_amount", 0.0)
                    
                return ActionResultSchema(
                    action=recommended_action,
                    result=result,
                    recovered_amount=recovered_amount
                )

        # Hash-based deterministic fallback (stable, reproducible output)
        hash_input = f"{case.case_id}:{recommended_action}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        modulo = hash_val % 100
        
        # Use case strategy probability to establish the success threshold
        prob = case.recovery_probability if case.recovery_probability is not None else 0.5
        threshold = int(prob * 100)

        if recommended_action == "STOP_RECOVERY":
            result = "STOPPED"
            recovered_amount = 0.0
        elif recommended_action == "ESCALATE_TO_HUMAN":
            result = "ESCALATED"
            recovered_amount = 0.0
        elif modulo < threshold:
            result = "SUCCESS"
            recovered_amount = payment.amount
        elif modulo < threshold + 15:
            result = "NO_RESPONSE"
            recovered_amount = 0.0
        else:
            result = "FAILED"
            recovered_amount = 0.0

        return ActionResultSchema(
            action=recommended_action,
            result=result,
            recovered_amount=recovered_amount
        )
