from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.services.batch_service import BatchService
from app.schemas.batch import (
    BatchCreateRequest,
    BatchResponseSchema,
    BatchImpactReportSchema,
    BatchCaseItemSchema
)
from app.models.batch import RecoveryBatch

router = APIRouter(prefix="/api/batches", tags=["batches"])

@router.post("", response_model=BatchResponseSchema)
def create_batch(request: BatchCreateRequest, db: Session = Depends(get_db)):
    """
    Creates a new recovery batch containing eligible pending cases.
    """
    try:
        batch_service = BatchService()
        batch = batch_service.create_batch(request.batch_name, request.case_ids, db)
        
        # Build response schema
        cases_list = [
            BatchCaseItemSchema(
                case_id=c.case_id,
                processing_status=c.processing_status,
                final_status=c.final_status,
                recovered_amount=c.recovered_amount,
                error_message=c.error_message
            ) for c in batch.cases
        ]
        
        return BatchResponseSchema(
            batch_id=batch.batch_id,
            batch_name=batch.batch_name,
            status=batch.status,
            total_cases=batch.total_cases,
            processed_cases=batch.processed_cases,
            approved_cases=batch.approved_cases,
            recovered_cases=batch.recovered_cases,
            stopped_cases=batch.stopped_cases,
            blocked_cases=batch.blocked_cases,
            hitl_cases=batch.hitl_cases,
            failed_cases=batch.failed_cases,
            ai_recommended_cases=batch.ai_recommended_cases or 0,
            scheduled_cases=batch.scheduled_cases or 0,
            executed_cases=batch.executed_cases or 0,
            total_outstanding_amount=batch.total_outstanding_amount,
            total_recovered_amount=batch.total_recovered_amount,
            total_expected_recovery_value=batch.total_expected_recovery_value,
            recovery_rate=batch.recovery_rate,
            created_at=batch.created_at.isoformat(),
            started_at=batch.started_at.isoformat() if batch.started_at else None,
            completed_at=batch.completed_at.isoformat() if batch.completed_at else None,
            cases=cases_list
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create batch: {str(e)}")

@router.post("/{batch_id}/run", response_model=BatchResponseSchema)
def run_batch(batch_id: str, db: Session = Depends(get_db)):
    """
    Runs the batch execution process synchronously.
    """
    try:
        batch_service = BatchService()
        batch = batch_service.process_batch(batch_id, db)
        
        cases_list = [
            BatchCaseItemSchema(
                case_id=c.case_id,
                processing_status=c.processing_status,
                final_status=c.final_status,
                recovered_amount=c.recovered_amount,
                error_message=c.error_message
            ) for c in batch.cases
        ]
        
        return BatchResponseSchema(
            batch_id=batch.batch_id,
            batch_name=batch.batch_name,
            status=batch.status,
            total_cases=batch.total_cases,
            processed_cases=batch.processed_cases,
            approved_cases=batch.approved_cases,
            recovered_cases=batch.recovered_cases,
            stopped_cases=batch.stopped_cases,
            blocked_cases=batch.blocked_cases,
            hitl_cases=batch.hitl_cases,
            failed_cases=batch.failed_cases,
            ai_recommended_cases=batch.ai_recommended_cases or 0,
            scheduled_cases=batch.scheduled_cases or 0,
            executed_cases=batch.executed_cases or 0,
            total_outstanding_amount=batch.total_outstanding_amount,
            total_recovered_amount=batch.total_recovered_amount,
            total_expected_recovery_value=batch.total_expected_recovery_value,
            recovery_rate=batch.recovery_rate,
            created_at=batch.created_at.isoformat(),
            started_at=batch.started_at.isoformat() if batch.started_at else None,
            completed_at=batch.completed_at.isoformat() if batch.completed_at else None,
            cases=cases_list
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process batch: {str(e)}")

@router.get("/{batch_id}", response_model=BatchResponseSchema)
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    """
    Gets the current status and metrics of a batch.
    """
    batch = db.query(RecoveryBatch).filter(RecoveryBatch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found.")
        
    cases_list = [
        BatchCaseItemSchema(
            case_id=c.case_id,
            processing_status=c.processing_status,
            final_status=c.final_status,
            recovered_amount=c.recovered_amount,
            error_message=c.error_message
        ) for c in batch.cases
    ]
    
    return BatchResponseSchema(
        batch_id=batch.batch_id,
        batch_name=batch.batch_name,
        status=batch.status,
        total_cases=batch.total_cases,
        processed_cases=batch.processed_cases,
        approved_cases=batch.approved_cases,
        recovered_cases=batch.recovered_cases,
        stopped_cases=batch.stopped_cases,
        blocked_cases=batch.blocked_cases,
        hitl_cases=batch.hitl_cases,
        failed_cases=batch.failed_cases,
        ai_recommended_cases=batch.ai_recommended_cases or 0,
        scheduled_cases=batch.scheduled_cases or 0,
        executed_cases=batch.executed_cases or 0,
        total_outstanding_amount=batch.total_outstanding_amount,
        total_recovered_amount=batch.total_recovered_amount,
        total_expected_recovery_value=batch.total_expected_recovery_value,
        recovery_rate=batch.recovery_rate,
        created_at=batch.created_at.isoformat(),
        started_at=batch.started_at.isoformat() if batch.started_at else None,
        completed_at=batch.completed_at.isoformat() if batch.completed_at else None,
        cases=cases_list
    )

@router.get("/{batch_id}/impact", response_model=BatchImpactReportSchema)
def get_batch_impact(batch_id: str, db: Session = Depends(get_db)):
    """
    Returns the comprehensive revenue impact and baseline comparison report for the batch.
    """
    try:
        batch_service = BatchService()
        return batch_service.get_batch_impact_report(batch_id, db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate impact report: {str(e)}")

@router.get("", response_model=List[BatchResponseSchema])
def list_batches(db: Session = Depends(get_db)):
    """
    Lists all recovery batches created in the system.
    """
    batches = db.query(RecoveryBatch).order_by(RecoveryBatch.created_at.desc()).all()
    results = []
    for batch in batches:
        cases_list = [
            BatchCaseItemSchema(
                case_id=c.case_id,
                processing_status=c.processing_status,
                final_status=c.final_status,
                recovered_amount=c.recovered_amount,
                error_message=c.error_message
            ) for c in batch.cases
        ]
        results.append(
            BatchResponseSchema(
                batch_id=batch.batch_id,
                batch_name=batch.batch_name,
                status=batch.status,
                total_cases=batch.total_cases,
                processed_cases=batch.processed_cases,
                approved_cases=batch.approved_cases,
                recovered_cases=batch.recovered_cases,
                stopped_cases=batch.stopped_cases,
                blocked_cases=batch.blocked_cases,
                hitl_cases=batch.hitl_cases,
                failed_cases=batch.failed_cases,
                ai_recommended_cases=batch.ai_recommended_cases or 0,
                scheduled_cases=batch.scheduled_cases or 0,
                executed_cases=batch.executed_cases or 0,
                total_outstanding_amount=batch.total_outstanding_amount,
                total_recovered_amount=batch.total_recovered_amount,
                total_expected_recovery_value=batch.total_expected_recovery_value,
                recovery_rate=batch.recovery_rate,
                created_at=batch.created_at.isoformat(),
                started_at=batch.started_at.isoformat() if batch.started_at else None,
                completed_at=batch.completed_at.isoformat() if batch.completed_at else None,
                cases=cases_list
            )
        )
    return results
