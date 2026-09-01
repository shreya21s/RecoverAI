from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult
from app.schemas.strategy import StrategyResult
from app.schemas.policy import PolicyResultSchema
from app.policies import rules

class PolicyEngine:
    def __init__(self):
        # 1. Terminal Rules
        self.terminal_rules = [
            rules.AlreadyRecoveredRule(),
            rules.TerminalCaseStatusRule(),
        ]
        
        # 2. Dispute / Risk Rules
        self.dispute_rules = [
            rules.CustomerDisputeRule()
        ]
        
        # 3. Hard Stopping & Economic Viability Rules
        self.stopping_rules = [
            rules.RepeatedFailureRule(),
            rules.MaxRetriesRule(),
            rules.MaxRemindersRule(),
            rules.LowRecoveryProbabilityRule(),
            rules.EconomicViabilityRule()
        ]
        
        # 4. Human-In-The-Loop Rules
        self.hitl_rules = [
            rules.HighValueTransactionRule(),
            rules.LowDiagnosisConfidenceRule(),
            rules.MultipleFailedAttemptsRule()
        ]

    def evaluate(
        self,
        case: RecoveryCase,
        payment: Payment,
        customer: Customer,
        diagnosis: DiagnosisResult,
        customer_analysis: CustomerAnalysisResult,
        strategy: StrategyResult
    ) -> PolicyResultSchema:
        """
        Runs the full check of terminal, dispute, stopping, and HITL rules.
        Precedence is strictly enforced.
        """
        # Step 1: Evaluate Terminal Rules
        for rule in self.terminal_rules:
            triggered, rule_name, reason, _, _ = rule.evaluate(
                case, payment, customer, diagnosis, customer_analysis, strategy
            )
            if triggered:
                return PolicyResultSchema(
                    decision="STOPPED",
                    action_allowed=False,
                    requires_human_approval=False,
                    triggered_rules=[rule_name],
                    reasons=[reason]
                )
                
        # Step 2: Evaluate Dispute Rules
        for rule in self.dispute_rules:
            triggered, rule_name, reason, _, _ = rule.evaluate(
                case, payment, customer, diagnosis, customer_analysis, strategy
            )
            if triggered:
                return PolicyResultSchema(
                    decision="HITL_REQUIRED",
                    action_allowed=False,
                    requires_human_approval=True,
                    triggered_rules=[rule_name],
                    reasons=[reason]
                )

        # Step 3: Evaluate Hard Stopping and Economic Rules
        for rule in self.stopping_rules:
            triggered, rule_name, reason, _, _ = rule.evaluate(
                case, payment, customer, diagnosis, customer_analysis, strategy
            )
            if triggered:
                decision = "BLOCKED" if "MAX_" in rule_name else "STOPPED"
                return PolicyResultSchema(
                    decision=decision,
                    action_allowed=False,
                    requires_human_approval=False,
                    triggered_rules=[rule_name],
                    reasons=[reason]
                )

        # Step 4: Evaluate HITL Rules (Collect all triggered reasons)
        triggered_hitl_rules = []
        hitl_reasons = []
        for rule in self.hitl_rules:
            triggered, rule_name, reason, _, _ = rule.evaluate(
                case, payment, customer, diagnosis, customer_analysis, strategy
            )
            if triggered:
                triggered_hitl_rules.append(rule_name)
                hitl_reasons.append(reason)
                
        if triggered_hitl_rules:
            return PolicyResultSchema(
                decision="HITL_REQUIRED",
                action_allowed=False,
                requires_human_approval=True,
                triggered_rules=triggered_hitl_rules,
                reasons=hitl_reasons
            )

        # Step 5: Default Approved
        return PolicyResultSchema(
            decision="APPROVED",
            action_allowed=True,
            requires_human_approval=False,
            triggered_rules=[],
            reasons=["All policy checks passed. Recovery action is approved for execution."]
        )
