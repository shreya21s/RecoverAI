from pydantic import BaseModel, Field
from typing import List

class CustomerAnalysisResult(BaseModel):
    customer_segment: str
    customer_quality_score: float = Field(..., ge=0.0, le=1.0)
    engagement_score: float = Field(..., ge=0.0, le=1.0)
    payment_reliability_score: float = Field(..., ge=0.0, le=1.0)
    historical_recovery_probability: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default=[])
