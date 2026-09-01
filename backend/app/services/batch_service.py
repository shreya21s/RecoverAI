import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.batch import RecoveryBatch, RecoveryBatchItem, BatchStatus
from app.models.recovery_case import RecoveryCase, RecoveryCaseStatus
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.graphs.recovery_graph import run_recovery_graph
from app.services.simulation_engine import SimulationEngine

logger = logging.getLogger("recoverai.batch_service")

class BatchService:
    def create_batch(self, name: str, case_ids: list = None, db: Session = None) -> RecoveryBatch:
        # Determine case eligibility
        # Exclude RECOVERED, STOPPED, WAITING_FOR_APPROVAL, ESCALATED
        ineligible_statuses = ["RECOVERED", "STOPPED", "WAITING_FOR_APPROVAL", "ESCALATED"]

        if case_ids is not None:
            # Explicit selection
            # Deduplicate case_ids
            case_ids = list(dict.fromkeys(case_ids))
            cases = db.query(RecoveryCase).filter(RecoveryCase.case_id.in_(case_ids)).all()
            found_ids = [c.case_id for c in cases]
            missing_ids = set(case_ids) - set(found_ids)
            if missing_ids:
                raise ValueError(f"Cases not found: {', '.join(missing_ids)}")
                
            for case in cases:
                if case.status in ineligible_statuses:
                    raise ValueError(f"Case {case.case_id} is ineligible because it is in a terminal or waiting state: {case.status}.")
        else:
            # Automatic selection
            cases = db.query(RecoveryCase).filter(
                ~RecoveryCase.status.in_(ineligible_statuses)
            ).all()

        if not cases:
            raise ValueError("No eligible recovery cases found to create a batch.")

        batch_id = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total outstanding amount
        total_outstanding = 0.0
        for case in cases:
            payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
            if payment:
                total_outstanding += payment.amount

        batch = RecoveryBatch(
            batch_id=batch_id,
            batch_name=name,
            status=BatchStatus.PENDING.value,
            total_cases=len(cases),
            total_outstanding_amount=total_outstanding,
            created_at=datetime.utcnow()
        )
        db.add(batch)
        db.commit()

        # Add batch items
        for case in cases:
            item = RecoveryBatchItem(
                batch_id=batch_id,
                case_id=case.case_id,
                processing_status="PENDING",
                recovered_amount=0.0
            )
            db.add(item)
            
            # Associate case with batch
            case.batch_id = batch_id
            
        db.commit()
        db.refresh(batch)
        return batch

    def process_batch(self, batch_id: str, db: Session) -> RecoveryBatch:
        batch = db.query(RecoveryBatch).filter(RecoveryBatch.batch_id == batch_id).first()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")
            
        if batch.status in [BatchStatus.RUNNING.value, BatchStatus.COMPLETED.value, BatchStatus.COMPLETED_WITH_ERRORS.value]:
            raise ValueError(f"Batch {batch_id} is already in state: {batch.status}.")

        batch.status = BatchStatus.RUNNING.value
        batch.started_at = datetime.utcnow()
        db.commit()

        items = db.query(RecoveryBatchItem).filter(RecoveryBatchItem.batch_id == batch_id).all()
        
        has_errors = False
        
        processed_count = 0
        approved_count = 0
        recovered_count = 0
        stopped_count = 0
        blocked_count = 0
        hitl_count = 0
        failed_count = 0
        
        # Part 11 Metrics
        ai_recommended_count = 0
        scheduled_count = 0
        executed_count = 0
        
        total_recovered_amount = 0.0
        total_expected_recovery_value = 0.0

        for item in items:
            case = db.query(RecoveryCase).filter(RecoveryCase.case_id == item.case_id).first()
            if not case:
                item.processing_status = "FAILED"
                item.error_message = "Case metadata not found in database."
                item.processed_at = datetime.utcnow()
                has_errors = True
                failed_count += 1
                db.commit()
                continue

            # Skip already terminal cases just in case
            if case.status in ["RECOVERED", "STOPPED"]:
                item.processing_status = "COMPLETED"
                item.final_status = case.status
                item.processed_at = datetime.utcnow()
                db.commit()
                continue

            try:
                # Log process start event
                audit_id = f"AUD-{case.case_id}-{uuid.uuid4().hex[:6]}"
                db_audit = AuditLog(
                    audit_id=audit_id,
                    case_id=case.case_id,
                    batch_id=batch_id,
                    actor_type="SYSTEM",
                    actor_name="BatchOrchestrator",
                    event_type="CASE_PROCESSING_STARTED",
                    decision_summary="Began processing case as part of batch.",
                    timestamp=datetime.utcnow()
                )
                db.add(db_audit)
                db.commit()

                # Call the recovery graph
                result_state = run_recovery_graph(case.case_id, db, human_decision=None, batch_id=batch_id)
                
                # Check for workflow errors
                if result_state.get("errors"):
                    raise ValueError(", ".join(result_state["errors"]))

                # Save case details
                policy = result_state.get("policy", {})
                action_result = result_state.get("action_result")
                
                item.processing_status = "COMPLETED"
                item.final_status = result_state["final_status"]
                item.processed_at = datetime.utcnow()
                
                # Update counters
                processed_count += 1
                if policy.get("decision") == "APPROVED":
                    approved_count += 1
                elif policy.get("decision") == "HITL_REQUIRED":
                    hitl_count += 1
                elif policy.get("decision") == "BLOCKED":
                    blocked_count += 1
                elif policy.get("decision") == "STOPPED":
                    stopped_count += 1
                
                strategy = result_state.get("strategy", {})
                if strategy:
                    total_expected_recovery_value += strategy.get("expected_recovery_value", 0.0)
                    
                    strategy_rec = strategy.get("recommended_action")
                    if strategy_rec and strategy_rec != "STOP_RECOVERY":
                        ai_recommended_count += 1

                if result_state.get("final_status") == "SCHEDULED":
                    scheduled_count += 1
                    
                if action_result:
                    item.recovered_amount = action_result.get("recovered_amount", 0.0)
                    total_recovered_amount += item.recovered_amount
                    if action_result.get("result") == "SUCCESS":
                        recovered_count += 1
                    
                    # Execution successfully dispatched or completed
                    if action_result.get("result") in ["SUCCESS", "FAILED", "PROCESSING", "SUCCEEDED"]:
                        executed_count += 1
                        
            except Exception as e:
                logger.error(f"Failed to process case {item.case_id} in batch {batch_id}: {str(e)}")
                item.processing_status = "FAILED"
                item.error_message = str(e)
                item.processed_at = datetime.utcnow()
                has_errors = True
                failed_count += 1
                
                # Log system error
                audit_id = f"AUD-{item.case_id}-{uuid.uuid4().hex[:6]}"
                db_audit = AuditLog(
                    audit_id=audit_id,
                    case_id=item.case_id,
                    batch_id=batch_id,
                    actor_type="SYSTEM",
                    actor_name="BatchOrchestrator",
                    event_type="ERROR",
                    decision_summary=f"Technical processing failure: {str(e)}",
                    timestamp=datetime.utcnow()
                )
                db.add(db_audit)
                
            db.commit()

        # Update batch aggregate metrics
        batch.processed_cases = processed_count
        batch.approved_cases = approved_count
        batch.recovered_cases = recovered_count
        batch.stopped_cases = stopped_count
        batch.blocked_cases = blocked_count
        batch.hitl_cases = hitl_count
        batch.failed_cases = failed_count
        batch.ai_recommended_cases = ai_recommended_count
        batch.scheduled_cases = scheduled_count
        batch.executed_cases = executed_count
        
        batch.total_recovered_amount = total_recovered_amount
        batch.total_expected_recovery_value = total_expected_recovery_value
        
        # Recovery Rate: (Recovered revenue / Total Outstanding Revenue) * 100
        if batch.total_outstanding_amount > 0:
            batch.recovery_rate = (total_recovered_amount / batch.total_outstanding_amount) * 100.0
            
        batch.status = BatchStatus.COMPLETED_WITH_ERRORS.value if has_errors else BatchStatus.COMPLETED.value
        batch.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(batch)
        return batch

    def get_batch_impact_report(self, batch_id: str, db: Session) -> dict:
        batch = db.query(RecoveryBatch).filter(RecoveryBatch.batch_id == batch_id).first()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        # Baseline calculation:
        # Every eligible case in the batch -> SMART_RETRY once.
        # Run simulated outcomes deterministically on identical starting cases.
        simulation_engine = SimulationEngine()
        baseline_recovered_revenue = 0.0
        
        items = db.query(RecoveryBatchItem).filter(RecoveryBatchItem.batch_id == batch_id).all()
        for item in items:
            case = db.query(RecoveryCase).filter(RecoveryCase.case_id == item.case_id).first()
            if not case:
                continue
            payment = db.query(Payment).filter(Payment.payment_id == case.payment_id).first()
            if not payment:
                continue
                
            # Simulate naive SMART_RETRY once
            sim_res = simulation_engine.execute_simulation(case, "SMART_RETRY", payment)
            if sim_res.result == "SUCCESS":
                baseline_recovered_revenue += sim_res.recovered_amount

        # Incremental revenue calculation
        recovered_revenue = batch.total_recovered_amount
        incremental = recovered_revenue - baseline_recovered_revenue
        
        # Calculate percentage improvement
        if baseline_recovered_revenue > 0:
            improvement_pct = (incremental / baseline_recovered_revenue) * 100.0
        else:
            improvement_pct = 0.0

        # Policy Block Rate: (Blocked + Stopped / Processed Cases) * 100
        total_processed = batch.processed_cases
        if total_processed > 0:
            policy_block_rate = ((batch.blocked_cases + batch.stopped_cases) / total_processed) * 100.0
            hitl_escalation_rate = (batch.hitl_cases / total_processed) * 100.0
        else:
            policy_block_rate = 0.0
            hitl_escalation_rate = 0.0

        # Accumulate stop/hitl rules and disagreements from processed cases
        stop_reasons = {}
        hitl_reasons = {}
        disagreement_cases = []
        
        for item in items:
            case = db.query(RecoveryCase).filter(RecoveryCase.case_id == item.case_id).first()
            if not case or not case.explanation_json:
                continue
                
            policy_exp = case.explanation_json.get("policy_explanation", {})
            decision = policy_exp.get("decision")
            triggered = policy_exp.get("triggered_rules", [])
            
            if decision in ["STOPPED", "BLOCKED"]:
                for rule in triggered:
                    stop_reasons[rule] = stop_reasons.get(rule, 0) + 1
            elif decision == "HITL_REQUIRED" or case.status == "WAITING_FOR_APPROVAL":
                for rule in triggered:
                    hitl_reasons[rule] = hitl_reasons.get(rule, 0) + 1
                    
            override_details = case.explanation_json.get("override_details", {})
            if override_details.get("is_overridden"):
                disagreement_cases.append({
                    "case_id": case.case_id,
                    "ai_recommendation": case.explanation_json.get("selected_strategy"),
                    "policy_decision": decision,
                    "reason": override_details.get("override_reason")
                })
                
        top_stop = [{"reason": k, "count": v} for k, v in sorted(stop_reasons.items(), key=lambda x: x[1], reverse=True)]
        top_hitl = [{"reason": k, "count": v} for k, v in sorted(hitl_reasons.items(), key=lambda x: x[1], reverse=True)]
        
        decision_insights = {
            "top_stop_reasons": top_stop,
            "top_hitl_reasons": top_hitl,
            "total_disagreements": len(disagreement_cases),
            "disagreement_cases": disagreement_cases
        }

        return {
            "batch_id": batch_id,
            "summary": {
                "total_cases": batch.total_cases,
                "processed_cases": batch.processed_cases,
                "recovered_cases": batch.recovered_cases,
                "stopped_cases": batch.stopped_cases,
                "hitl_cases": batch.hitl_cases,
                "failed_cases": batch.failed_cases,
                "ai_recommended_cases": batch.ai_recommended_cases or 0,
                "scheduled_cases": batch.scheduled_cases or 0,
                "executed_cases": batch.executed_cases or 0
            },
            "financial_impact": {
                "total_outstanding_revenue": batch.total_outstanding_amount,
                "eligible_outstanding_revenue": batch.total_outstanding_amount,
                "recovered_revenue": recovered_revenue,
                "expected_recovery_value": batch.total_expected_recovery_value,
                "unrecovered_revenue": max(0.0, batch.total_outstanding_amount - recovered_revenue),
                "recovery_rate": batch.recovery_rate
            },
            "safety_metrics": {
                "policy_block_rate": policy_block_rate,
                "hitl_escalation_rate": hitl_escalation_rate
            },
            "baseline_comparison": {
                "baseline_recovered_revenue": baseline_recovered_revenue,
                "recoverai_recovered_revenue": recovered_revenue,
                "incremental_revenue": incremental,
                "improvement_percentage": improvement_pct
            },
            "decision_insights": decision_insights
        }
