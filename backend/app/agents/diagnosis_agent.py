from datetime import datetime
from langchain_core.runnables import RunnableConfig
from app.agents.state import RecoveryState
from app.services.diagnosis_service import DiagnosisService
from app.services.ai_enrichment import AIEnrichmentService
from app.models.payment import Payment

def diagnosis_agent_node(state: RecoveryState, config: RunnableConfig) -> dict:
    trace = list(state.get("agent_trace", []))
    db = config["configurable"]["db"]
    
    payment_id = state["payment_data"]["payment_id"]
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    
    diagnosis_service = DiagnosisService()
    diag_res = diagnosis_service.diagnose_payment(payment)
    
    ai_service = AIEnrichmentService()
    ai_sum = ai_service.get_diagnosis_summary(
        diag_res.failure_category,
        diag_res.confidence,
        diag_res.evidence
    )
    
    diagnosis_dict = {
        "failure_category": diag_res.failure_category,
        "confidence": diag_res.confidence,
        "evidence": diag_res.evidence,
        "recommended_direction": diag_res.recommended_direction,
        "ai_summary": ai_sum
    }
    
    trace.append({
        "step": "diagnosis_agent",
        "status": "completed",
        "summary": ai_sum,
        "triggered_rules": None,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"diagnosis": diagnosis_dict, "agent_trace": trace}
