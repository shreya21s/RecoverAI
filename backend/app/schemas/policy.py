from pydantic import BaseModel, Field
from typing import List

class PolicyResultSchema(BaseModel):
    decision: str = Field(..., description="APPROVED, BLOCKED, STOPPED, or HITL_REQUIRED")
    action_allowed: bool
    requires_human_approval: bool
    triggered_rules: List[str] = Field(default=[])
    reasons: List[str] = Field(default=[])
