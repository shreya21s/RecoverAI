from datetime import datetime
from langchain_core.runnables import RunnableConfig
from app.agents.state import RecoveryState
from app.services.customer_analysis_service import CustomerAnalysisService
from app.services.ai_enrichment import AIEnrichmentService
from app.models.customer import Customer

def customer_agent_node(state: RecoveryState, config: RunnableConfig) -> dict:
    trace = list(state.get("agent_trace", []))
    db = config["configurable"]["db"]
    
    customer_id = state["customer_data"]["customer_id"]
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    customer_analysis_service = CustomerAnalysisService()
    cust_res = customer_analysis_service.analyze_customer(customer)
    
    ai_service = AIEnrichmentService()
    ai_sum = ai_service.get_customer_summary(
        cust_res.customer_segment,
        cust_res.customer_quality_score,
        cust_res.payment_reliability_score,
        cust_res.engagement_score
    )
    
    customer_analysis_dict = {
        "customer_segment": cust_res.customer_segment,
        "customer_quality_score": cust_res.customer_quality_score,
        "engagement_score": cust_res.engagement_score,
        "payment_reliability_score": cust_res.payment_reliability_score,
        "historical_recovery_probability": cust_res.historical_recovery_probability,
        "evidence": cust_res.evidence,
        "ai_summary": ai_sum
    }
    
    trace.append({
        "step": "customer_agent",
        "status": "completed",
        "summary": ai_sum,
        "triggered_rules": None,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"customer_analysis": customer_analysis_dict, "agent_trace": trace}
