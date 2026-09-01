from pydantic import BaseModel, Field
from typing import List

class StrategyResult(BaseModel):
    recommended_action: str
    recovery_probability: float = Field(..., ge=0.0, le=1.0)
    expected_recovery_value: float = Field(..., ge=0.0)
    estimated_action_cost: float = Field(..., ge=0.0)
    reason: str
    alternative_actions: List[str] = Field(default=[])
