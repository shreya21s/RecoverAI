from datetime import datetime
from app.agents.state import RecoveryState
from app.services.strategy_service import StrategyService
from app.services.ai_enrichment import AIEnrichmentService
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult

def strategy_agent_node(state: RecoveryState) -> dict:
    trace = list(state.get("agent_trace", []))
    
    # Reconstruct schemas
    diag_dict = state["diagnosis"]
    analysis_dict = state["customer_analysis"]
    pay_dict = state["payment_data"]
    
    diagnosis = DiagnosisResult(
        failure_category=diag_dict["failure_category"],
        confidence=diag_dict["confidence"],
        evidence=diag_dict["evidence"],
        recommended_direction=diag_dict["recommended_direction"]
    )
    
    customer_analysis = CustomerAnalysisResult(
        customer_segment=analysis_dict["customer_segment"],
        customer_quality_score=analysis_dict["customer_quality_score"],
        engagement_score=analysis_dict["engagement_score"],
        payment_reliability_score=analysis_dict["payment_reliability_score"],
        historical_recovery_probability=analysis_dict["historical_recovery_probability"],
        evidence=analysis_dict["evidence"]
    )
    
    strategy_service = StrategyService()
    strat_res = strategy_service.determine_strategy(
        diagnosis,
        customer_analysis,
        pay_dict["amount"],
        pay_dict["retry_count"],
        pay_dict["reminder_count"]
    )
    
    ai_service = AIEnrichmentService()
    ai_sum = ai_service.get_strategy_summary(
        strat_res.recommended_action,
        strat_res.recovery_probability,
        strat_res.expected_recovery_value,
        strat_res.estimated_action_cost
    )
    
    strategy_dict = {
        "recommended_action": strat_res.recommended_action,
        "recovery_probability": strat_res.recovery_probability,
        "expected_recovery_value": strat_res.expected_recovery_value,
        "estimated_action_cost": strat_res.estimated_action_cost,
        "reason": strat_res.reason,
        "alternative_actions": strat_res.alternative_actions,
        "ai_summary": ai_sum
    }
    
    trace.append({
        "step": "strategy_agent",
        "status": "completed",
        "summary": ai_sum,
        "triggered_rules": None,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"strategy": strategy_dict, "agent_trace": trace}
