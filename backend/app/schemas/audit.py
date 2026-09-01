from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AuditEventSchema(BaseModel):
    audit_id: str
    case_id: str
    batch_id: Optional[str] = None
    timestamp: str
    actor_type: str
    actor_name: str
    event_type: str
    decision_summary: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
