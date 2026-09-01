from datetime import datetime
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from app.agents.state import RecoveryState
from app.agents.supervisor import supervisor_node
from app.agents.diagnosis_agent import diagnosis_agent_node
from app.agents.customer_agent import customer_agent_node
from app.agents.strategy_agent import strategy_agent_node

from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction

from app.services.simulation_engine import SimulationEngine
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult
from app.schemas.strategy import StrategyResult
from app.policies.policy_engine import PolicyEngine

import uuid
from app.models.audit_log import AuditLog

def log_audit_event(
    case_id: str,
    event_type: str,
    actor_type: str,
    actor_name: str,
    summary: str,
    metadata: dict,
    config: RunnableConfig
):
    db: Session = config["configurable"]["db"]
    batch_id = config.get("configurable", {}).get("batch_id")
    
    audit_id = f"AUD-{case_id}-{uuid.uuid4().hex[:6]}"
    db_audit = AuditLog(
        audit_id=audit_id,
        case_id=case_id,
        batch_id=batch_id,
        actor_type=actor_type,
        actor_name=actor_name,
        event_type=event_type,
        decision_summary=summary[:255] if summary else None,
        metadata_json=metadata,
        timestamp=datetime.utcnow()
    )
    db.add(db_audit)
    db.commit()

from app.services.explainability_service import ExplainabilityService
explainability_service = ExplainabilityService()

def save_explanation_from_state(state: RecoveryState, config: RunnableConfig) -> dict:
    db: Session = config["configurable"]["db"]
    case_id = state["case_id"]
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        return None
    payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
    if not payment:
        return None
    customer = db.query(Customer).filter(Customer.customer_id == payment.customer_id).first()
    if not customer:
        return None
    
    diag_dict = state.get("diagnosis")
    analysis_dict = state.get("customer_analysis")
    strat_dict = state.get("strategy")
    policy_dict = state.get("policy")
    
    if not (diag_dict and analysis_dict and strat_dict and policy_dict):
        return None
        
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
    
    strategy = StrategyResult(
        recommended_action=strat_dict["recommended_action"],
        recovery_probability=strat_dict["recovery_probability"],
        expected_recovery_value=strat_dict["expected_recovery_value"],
        estimated_action_cost=strat_dict["estimated_action_cost"],
        reason=strat_dict["reason"],
        alternative_actions=strat_dict["alternative_actions"]
    )
    
    explanation = explainability_service.generate_explanation(
        case=case,
        payment=payment,
        customer=customer,
        diagnosis=diagnosis,
        customer_analysis=customer_analysis,
        strategy=strategy,
        policy_decision=policy_dict["decision"],
        triggered_rules=policy_dict["triggered_rules"]
    )
    
    case.explanation_json = explanation
    db.commit()
    db.refresh(case)
    
    # Log DECISION_EXPLAINED audit event
    log_audit_event(
        case_id=case_id,
        event_type="DECISION_EXPLAINED",
        actor_type="SYSTEM",
        actor_name="ExplainabilityService",
        summary=f"Decision explanation generated for strategy {explanation.get('selected_strategy')}.",
        metadata={
            "selected_strategy": explanation.get("selected_strategy"),
            "policy_decision": explanation.get("policy_explanation", {}).get("decision"),
            "triggered_rules": explanation.get("policy_explanation", {}).get("triggered_rules", [])
        },
        config=config
    )
    
    return explanation

def wrapped_diagnosis_agent_node(state: RecoveryState, config: RunnableConfig) -> dict:
    result = diagnosis_agent_node(state, config)
    diag = result["diagnosis"]
    log_audit_event(
        case_id=state["case_id"],
        event_type="DIAGNOSIS_COMPLETED",
        actor_type="AGENT",
        actor_name="DiagnosisAgent",
        summary=f"Payment failure categorized as {diag['failure_category']} with {diag['confidence']*100:.1f}% confidence.",
        metadata={"failure_category": diag["failure_category"], "confidence": diag["confidence"]},
        config=config
    )
    return result

def wrapped_customer_agent_node(state: RecoveryState, config: RunnableConfig) -> dict:
    result = customer_agent_node(state, config)
    analysis = result["customer_analysis"]
    log_audit_event(
        case_id=state["case_id"],
        event_type="CUSTOMER_ANALYSIS_COMPLETED",
        actor_type="AGENT",
        actor_name="CustomerAgent",
        summary=f"Analyzed profile for segment: {analysis['customer_segment']}. Reliability score: {analysis['payment_reliability_score']}.",
        metadata={
            "customer_segment": analysis["customer_segment"],
            "customer_quality_score": analysis["customer_quality_score"],
            "payment_reliability_score": analysis["payment_reliability_score"]
        },
        config=config
    )
    return result

def wrapped_strategy_agent_node(state: RecoveryState, config: RunnableConfig) -> dict:
    result = strategy_agent_node(state)
    strategy = result["strategy"]
    log_audit_event(
        case_id=state["case_id"],
        event_type="STRATEGY_SELECTED",
        actor_type="AGENT",
        actor_name="StrategyAgent",
        summary=f"Selected recovery action: {strategy['recommended_action']}. Expected recovery value: {strategy['expected_recovery_value']}.",
        metadata={
            "recommended_action": strategy["recommended_action"],
            "recovery_probability": strategy["recovery_probability"],
            "expected_recovery_value": strategy["expected_recovery_value"]
        },
        config=config
    )
    return result

def load_case_node(state: RecoveryState, config: RunnableConfig) -> dict:
    trace = list(state.get("agent_trace", []))
    errors = list(state.get("errors", []))
    db: Session = config["configurable"]["db"]
    
    case_id = state["case_id"]
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        errors.append(f"Case {case_id} not found.")
        trace.append({
            "step": "load_case",
            "status": "failed",
            "summary": f"Failed to load case: {case_id} not found.",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {"errors": errors, "agent_trace": trace}
        
    payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
    if not payment:
        errors.append(f"Payment not found for case {case_id}.")
        trace.append({
            "step": "load_case",
            "status": "failed",
            "summary": f"Failed to load payment context for case {case_id}.",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {"errors": errors, "agent_trace": trace}
        
    customer = db.query(Customer).filter(Customer.customer_id == payment.customer_id).first()
    if not customer:
        errors.append(f"Customer not found for payment {payment.payment_id}.")
        trace.append({
            "step": "load_case",
            "status": "failed",
            "summary": f"Failed to load customer context for payment {payment.payment_id}.",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {"errors": errors, "agent_trace": trace}
        
    payment_data = {
        "payment_id": payment.payment_id,
        "customer_id": payment.customer_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "payment_method": payment.payment_method,
        "status": payment.status,
        "failure_code": payment.failure_code,
        "retry_count": payment.retry_count,
        "reminder_count": payment.reminder_count,
        "is_disputed": payment.is_disputed,
        "is_recovered": payment.is_recovered
    }
    
    customer_data = {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "segment": customer.segment,
        "lifetime_value": customer.lifetime_value,
        "total_successful_payments": customer.total_successful_payments,
        "total_failed_payments": customer.total_failed_payments,
        "average_payment_amount": customer.average_payment_amount,
        "engagement_score": customer.engagement_score
    }
    
    log_audit_event(
        case_id=case_id,
        event_type="CASE_PROCESSING_STARTED",
        actor_type="SYSTEM",
        actor_name="RecoveryOrchestrator",
        summary="Loaded case, payment, and customer details successfully. Recovery flow started.",
        metadata={},
        config=config
    )
    
    trace.append({
        "step": "load_case",
        "status": "completed",
        "summary": "Loaded case, payment, and customer details successfully.",
        "triggered_rules": None,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "payment_data": payment_data,
        "customer_data": customer_data,
        "agent_trace": trace
    }

def policy_node(state: RecoveryState, config: RunnableConfig) -> dict:
    trace = list(state.get("agent_trace", []))
    db: Session = config["configurable"]["db"]
    
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == state["case_id"]).first()
    payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
    customer = db.query(Customer).filter(Customer.customer_id == payment.customer_id).first()
    
    diag_dict = state["diagnosis"]
    analysis_dict = state["customer_analysis"]
    strat_dict = state["strategy"]
    
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
    
    strategy = StrategyResult(
        recommended_action=strat_dict["recommended_action"],
        recovery_probability=strat_dict["recovery_probability"],
        expected_recovery_value=strat_dict["expected_recovery_value"],
        estimated_action_cost=strat_dict["estimated_action_cost"],
        reason=strat_dict["reason"],
        alternative_actions=strat_dict["alternative_actions"]
    )
    
    policy_engine = PolicyEngine()
    policy_res = policy_engine.evaluate(
        case, payment, customer, diagnosis, customer_analysis, strategy
    )
    
    policy_dict = {
        "decision": policy_res.decision,
        "action_allowed": policy_res.action_allowed,
        "requires_human_approval": policy_res.requires_human_approval,
        "triggered_rules": policy_res.triggered_rules,
        "reasons": policy_res.reasons
    }
    
    human_decision = state.get("human_decision")
    if human_decision and human_decision.get("decision") == "APPROVED":
        # Log manual human approval
        log_audit_event(
            case_id=case.case_id,
            event_type="HUMAN_APPROVED",
            actor_type="HUMAN",
            actor_name=human_decision.get("reviewer_id", "admin"),
            summary=f"Human reviewer approved recovery. Reason: {human_decision.get('reason')}",
            metadata={"reviewer_id": human_decision.get("reviewer_id"), "reason": human_decision.get("reason")},
            config=config
        )
        
        trace.append({
            "step": "human_review",
            "status": "approved",
            "summary": f"Human reviewer approved controlled recovery. Reason: {human_decision.get('reason')}",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if policy_res.decision == "HITL_REQUIRED":
            soft_rules = {"HIGH_VALUE_TRANSACTION", "LOW_DIAGNOSIS_CONFIDENCE", "MULTIPLE_FAILED_ATTEMPTS"}
            all_soft = all(rule in soft_rules for rule in policy_res.triggered_rules)
            if all_soft:
                policy_dict["decision"] = "APPROVED"
                policy_dict["action_allowed"] = True
                policy_dict["requires_human_approval"] = False
                
                log_audit_event(
                    case_id=case.case_id,
                    event_type="POLICY_REVALIDATED",
                    actor_type="POLICY_ENGINE",
                    actor_name="PolicyEngine",
                    summary=f"Policy revalidated successfully. Bypassed soft rules: {', '.join(policy_res.triggered_rules)}.",
                    metadata={"decision": "APPROVED", "override": True, "bypassed_rules": policy_res.triggered_rules},
                    config=config
                )
                
                trace.append({
                    "step": "policy_revalidation",
                    "status": "approved",
                    "summary": f"Policy revalidation completed successfully. Soft rules overridden: {', '.join(policy_res.triggered_rules)}.",
                    "triggered_rules": policy_res.triggered_rules,
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                non_soft = [rule for rule in policy_res.triggered_rules if rule not in soft_rules]
                log_audit_event(
                    case_id=case.case_id,
                    event_type="POLICY_REVALIDATED",
                    actor_type="POLICY_ENGINE",
                    actor_name="PolicyEngine",
                    summary=f"Policy revalidation failed. Hard rules violated: {', '.join(non_soft)}.",
                    metadata={"decision": "HITL_REQUIRED", "override": False, "violated_hard_rules": non_soft},
                    config=config
                )
                
                trace.append({
                    "step": "policy_revalidation",
                    "status": "failed",
                    "summary": f"Policy revalidation failed. Hard rules violated: {', '.join(non_soft)}",
                    "triggered_rules": non_soft,
                    "timestamp": datetime.utcnow().isoformat()
                })
        else:
            log_audit_event(
                case_id=case.case_id,
                event_type="POLICY_REVALIDATED",
                actor_type="POLICY_ENGINE",
                actor_name="PolicyEngine",
                summary=f"Policy revalidation completed. Outcome remains: {policy_res.decision}",
                metadata={"decision": policy_res.decision},
                config=config
            )
            
            trace.append({
                "step": "policy_revalidation",
                "status": "completed",
                "summary": f"Policy revalidation completed. Decision remains: {policy_res.decision}.",
                "triggered_rules": policy_res.triggered_rules,
                "timestamp": datetime.utcnow().isoformat()
            })
    else:
        # Initial policy evaluations
        triggered_rules = policy_res.triggered_rules
        if policy_res.decision == "APPROVED":
            summary = "Action approved. No stopping rules triggered."
            log_audit_event(
                case_id=case.case_id,
                event_type="POLICY_APPROVED",
                actor_type="POLICY_ENGINE",
                actor_name="PolicyEngine",
                summary="Recovery strategy approved by policy engine rules.",
                metadata={"decision": "APPROVED", "triggered_rules": triggered_rules},
                config=config
            )
        elif policy_res.decision == "HITL_REQUIRED":
            summary = f"Human approval required due to rules: {', '.join(triggered_rules)}."
            log_audit_event(
                case_id=case.case_id,
                event_type="POLICY_HITL_REQUIRED",
                actor_type="POLICY_ENGINE",
                actor_name="PolicyEngine",
                summary=f"Action blocked pending human reviewer review: {', '.join(triggered_rules)}",
                metadata={"decision": "HITL_REQUIRED", "triggered_rules": triggered_rules},
                config=config
            )
        else:
            summary = f"Recovery blocked/stopped by policy engine: {', '.join(triggered_rules)}."
            log_audit_event(
                case_id=case.case_id,
                event_type=f"POLICY_{policy_res.decision}",
                actor_type="POLICY_ENGINE",
                actor_name="PolicyEngine",
                summary=f"Recovery strategy blocked or stopped: {', '.join(triggered_rules)}",
                metadata={"decision": policy_res.decision, "triggered_rules": triggered_rules},
                config=config
            )
            
        trace.append({
            "step": "policy_engine",
            "status": "completed",
            "summary": summary,
            "triggered_rules": triggered_rules,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    explanation = save_explanation_from_state({**state, "policy": policy_dict}, config)
    return {"policy": policy_dict, "agent_trace": trace, "explanation": explanation}

def execution_node(state: RecoveryState, config: RunnableConfig) -> dict:
    trace = list(state.get("agent_trace", []))
    db: Session = config["configurable"]["db"]
    
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == state["case_id"]).first()
    
    strat_dict = state["strategy"]
    recommended_action = strat_dict["recommended_action"]
    
    case.recovery_probability = strat_dict["recovery_probability"]
    case.expected_recovery_value = strat_dict["expected_recovery_value"]
    case.estimated_action_cost = strat_dict["estimated_action_cost"]
    case.current_strategy = recommended_action
    case.updated_at = datetime.utcnow()
    db.commit()
    
    from app.services.recovery_execution_service import RecoveryExecutionService
    execution_service = RecoveryExecutionService()
    db_action = execution_service.execute_recovery(case.case_id, recommended_action, db)
    
    action_result_dict = {
        "action": db_action.action_type,
        "result": "SUCCESS" if db_action.status == "SUCCEEDED" else ("STOPPED" if db_action.status == "BLOCKED" else db_action.status),
        "recovered_amount": db_action.recovered_amount
    }
    
    trace.append({
        "step": "execution_node",
        "status": "completed",
        "summary": f"Recovery action executed: {recommended_action} result status was {db_action.status}.",
        "triggered_rules": None,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    explanation = save_explanation_from_state({
        **state,
        "action_result": action_result_dict,
        "final_status": case.status
    }, config)
    return {
        "action_result": action_result_dict,
        "final_status": case.status,
        "agent_trace": trace,
        "explanation": explanation
    }

def hitl_pending_node(state: RecoveryState, config: RunnableConfig) -> dict:
    trace = list(state.get("agent_trace", []))
    db: Session = config["configurable"]["db"]
    
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == state["case_id"]).first()
    payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
    
    case.status = "WAITING_FOR_APPROVAL"
    case.requires_human_approval = True
    
    if payment.is_disputed:
        case.status = "ESCALATED"
        
    from app.models.approval import HumanApproval, ApprovalDecision
    existing = db.query(HumanApproval).filter(
        HumanApproval.case_id == case.case_id,
        HumanApproval.decision == ApprovalDecision.PENDING.value
    ).first()
    
    if not existing:
        import uuid
        approval_id = f"APP-{case.case_id}-{uuid.uuid4().hex[:6]}"
        db_approval = HumanApproval(
            approval_id=approval_id,
            case_id=case.case_id,
            decision=ApprovalDecision.PENDING.value,
            created_at=datetime.utcnow()
        )
        db.add(db_approval)
        
    db.commit()
    db.refresh(case)
    
    log_audit_event(
        case_id=case.case_id,
        event_type="WAITING_FOR_APPROVAL",
        actor_type="SYSTEM",
        actor_name="RecoveryOrchestrator",
        summary=f"Automated flow paused. Case marked as {case.status}.",
        metadata={},
        config=config
    )
    
    trace.append({
        "step": "hitl_pending",
        "status": "waiting_for_approval",
        "summary": f"Automated execution paused pending human approval. Case marked as {case.status}.",
        "triggered_rules": None,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "final_status": case.status,
        "agent_trace": trace
    }

def finalize_node(state: RecoveryState, config: RunnableConfig) -> dict:
    trace = list(state.get("agent_trace", []))
    errors = state.get("errors", [])
    db: Session = config["configurable"]["db"]
    
    case_id = state["case_id"]
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    
    human_decision = state.get("human_decision")
    if human_decision and human_decision.get("decision") == "REJECTED":
        if case:
            case.status = "STOPPED"
            case.requires_human_approval = False
            db.commit()
            db.refresh(case)
            
        log_audit_event(
            case_id=case_id,
            event_type="HUMAN_REJECTED",
            actor_type="HUMAN",
            actor_name=human_decision.get("reviewer_id", "admin"),
            summary=f"Recovery stopped by human reviewer. Reason: {human_decision.get('reason')}",
            metadata={"reviewer_id": human_decision.get("reviewer_id"), "reason": human_decision.get("reason")},
            config=config
        )
        
        log_audit_event(
            case_id=case_id,
            event_type="CASE_COMPLETED",
            actor_type="SYSTEM",
            actor_name="RecoveryOrchestrator",
            summary="Case closed with status: STOPPED.",
            metadata={"final_status": "STOPPED"},
            config=config
        )
        
        trace.append({
            "step": "human_review",
            "status": "rejected",
            "summary": f"Recovery stopped by human reviewer. Reason: {human_decision.get('reason')}",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {
            "final_status": "STOPPED",
            "agent_trace": trace
        }
        
    if errors:
        final_status = "FAILED"
        log_audit_event(
            case_id=case_id,
            event_type="ERROR",
            actor_type="SYSTEM",
            actor_name="RecoveryOrchestrator",
            summary=f"Recovery workflow failed: {', '.join(errors)}",
            metadata={"errors": errors},
            config=config
        )
        
        trace.append({
            "step": "finalize",
            "status": "failed",
            "summary": f"Workflow failed with errors: {', '.join(errors)}",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
    elif case:
        policy = state.get("policy")
        if policy and policy["decision"] in ["STOPPED", "BLOCKED"]:
            payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
            case.status = "STOPPED"
            if payment.is_recovered:
                case.status = "RECOVERED"
            db.commit()
            db.refresh(case)
            
        final_status = case.status
        log_audit_event(
            case_id=case_id,
            event_type="CASE_COMPLETED",
            actor_type="SYSTEM",
            actor_name="RecoveryOrchestrator",
            summary=f"Recovery workflow finished. Case status: {final_status}.",
            metadata={"final_status": final_status},
            config=config
        )
        
        trace.append({
            "step": "finalize",
            "status": "completed",
            "summary": f"Recovery workflow finished. Case final status: {final_status}.",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
    else:
        final_status = "FAILED"
        log_audit_event(
            case_id=case_id,
            event_type="ERROR",
            actor_type="SYSTEM",
            actor_name="RecoveryOrchestrator",
            summary="Recovery workflow finished but case metadata was missing.",
            metadata={},
            config=config
        )
        
        trace.append({
            "step": "finalize",
            "status": "failed",
            "summary": "Workflow finished but case metadata was missing.",
            "triggered_rules": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    explanation = save_explanation_from_state({
        **state,
        "final_status": final_status
    }, config)
    return {
        "final_status": final_status,
        "agent_trace": trace,
        "explanation": explanation
    }

def supervisor_routing(state: RecoveryState):
    if state.get("errors"):
        return "finalize"
    return "diagnosis_agent"

def policy_routing(state: RecoveryState):
    if state.get("errors"):
        return "finalize"
        
    human_decision = state.get("human_decision")
    if human_decision and human_decision.get("decision") == "REJECTED":
        return "finalize"
        
    policy = state.get("policy")
    if not policy:
        return "finalize"
        
    decision = policy["decision"]
    if decision == "APPROVED":
        return "execution_node"
    elif decision == "HITL_REQUIRED":
        return "hitl_pending_node"
    elif decision in ["STOPPED", "BLOCKED"]:
        return "finalize"
    else:
        return "finalize"

# Compile LangGraph StateGraph workflow
workflow = StateGraph(RecoveryState)

workflow.add_node("load_case", load_case_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("diagnosis_agent", wrapped_diagnosis_agent_node)
workflow.add_node("customer_agent", wrapped_customer_agent_node)
workflow.add_node("strategy_agent", wrapped_strategy_agent_node)
workflow.add_node("policy_node", policy_node)
workflow.add_node("execution_node", execution_node)
workflow.add_node("hitl_pending_node", hitl_pending_node)
workflow.add_node("finalize", finalize_node)

workflow.set_entry_point("load_case")

workflow.add_edge("load_case", "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    supervisor_routing,
    {
        "finalize": "finalize",
        "diagnosis_agent": "diagnosis_agent"
    }
)
workflow.add_edge("diagnosis_agent", "customer_agent")
workflow.add_edge("customer_agent", "strategy_agent")
workflow.add_edge("strategy_agent", "policy_node")
workflow.add_conditional_edges(
    "policy_node",
    policy_routing,
    {
        "execution_node": "execution_node",
        "hitl_pending_node": "hitl_pending_node",
        "finalize": "finalize"
    }
)
workflow.add_edge("execution_node", "finalize")
workflow.add_edge("hitl_pending_node", "finalize")
workflow.add_edge("finalize", END)

app_graph = workflow.compile()

def run_recovery_graph(case_id: str, db: Session, human_decision: dict = None, batch_id: str = None) -> dict:
    initial_state = {
        "case_id": case_id,
        "payment_data": None,
        "customer_data": None,
        "diagnosis": None,
        "customer_analysis": None,
        "strategy": None,
        "policy": None,
        "action_result": None,
        "final_status": None,
        "agent_trace": [],
        "errors": [],
        "human_decision": human_decision
    }
    
    result_state = app_graph.invoke(
        initial_state,
        config={"configurable": {"db": db, "batch_id": batch_id}}
    )
    return result_state
