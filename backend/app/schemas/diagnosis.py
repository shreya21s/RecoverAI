from pydantic import BaseModel, Field
from typing import List

class DiagnosisResult(BaseModel):
    failure_category: str = Field(..., description="E.g. TEMPORARY_FAILURE, INSUFFICIENT_FUNDS, etc.")
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default=[])
    recommended_direction: str = Field(..., description="The suggested recovery strategy direction.")
