from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.schemas.common import BaseSchema

class RecoveryCaseBase(BaseModel):
    payment_id: str = Field(..., max_length=50)
    batch_id: Optional[str] = Field(None, max_length=50)
    status: str = Field("PENDING", max_length=50)
    current_strategy: Optional[str] = Field(None, max_length=50)
    recovery_probability: float = 0.0
    expected_recovery_value: float = 0.0
    estimated_action_cost: float = 0.0
    requires_human_approval: bool = False
    metadata_json: Optional[dict] = None
    explanation_json: Optional[dict] = None

class RecoveryCaseCreate(RecoveryCaseBase):
    case_id: str = Field(..., max_length=50)

class RecoveryCase(RecoveryCaseBase, BaseSchema):
    case_id: str
    created_at: datetime
    updated_at: datetime
