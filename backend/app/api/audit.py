from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditEventSchema

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/cases/{case_id}", response_model=List[AuditEventSchema])
def get_case_audit_trail(case_id: str, db: Session = Depends(get_db)):
    """
    Returns the ordered, chronological audit trail events for a specific case.
    """
    events = db.query(AuditLog).filter(
        AuditLog.case_id == case_id
    ).order_by(AuditLog.timestamp.asc()).all()
    
    return [
        AuditEventSchema(
            audit_id=e.audit_id,
            case_id=e.case_id,
            batch_id=e.batch_id,
            timestamp=e.timestamp.isoformat(),
            actor_type=e.actor_type,
            actor_name=e.actor_name,
            event_type=e.event_type,
            decision_summary=e.decision_summary,
            metadata_json=e.metadata_json
        ) for e in events
    ]

@router.get("/batches/{batch_id}", response_model=List[AuditEventSchema])
def get_batch_audit_trail(batch_id: str, db: Session = Depends(get_db)):
    """
    Returns the ordered, chronological audit trail events associated with a batch.
    """
    events = db.query(AuditLog).filter(
        AuditLog.batch_id == batch_id
    ).order_by(AuditLog.timestamp.asc()).all()
    
    return [
        AuditEventSchema(
            audit_id=e.audit_id,
            case_id=e.case_id,
            batch_id=e.batch_id,
            timestamp=e.timestamp.isoformat(),
            actor_type=e.actor_type,
            actor_name=e.actor_name,
            event_type=e.event_type,
            decision_summary=e.decision_summary,
            metadata_json=e.metadata_json
        ) for e in events
    ]
