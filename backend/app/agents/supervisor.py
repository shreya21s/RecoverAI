from datetime import datetime
from app.agents.state import RecoveryState

def supervisor_node(state: RecoveryState) -> dict:
    trace = list(state.get("agent_trace", []))
    errors = list(state.get("errors", []))
    
    if not state.get("case_id"):
        errors.append("Supervisor validation failed: case_id is missing.")
        trace.append({
            "step": "supervisor",
            "status": "failed",
            "summary": "Validation failed: case_id is missing.",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {"errors": errors, "agent_trace": trace}
        
    if not state.get("payment_data") or not state.get("customer_data"):
        errors.append("Supervisor validation failed: payment or customer context is missing.")
        trace.append({
            "step": "supervisor",
            "status": "failed",
            "summary": "Validation failed: required payment/customer context is missing.",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {"errors": errors, "agent_trace": trace}
        
    trace.append({
        "step": "supervisor",
        "status": "completed",
        "summary": "Context validation successful. Beginning diagnosis and profiling.",
        "triggered_rules": None,
        "timestamp": datetime.utcnow().isoformat()
    })
    return {"agent_trace": trace}
