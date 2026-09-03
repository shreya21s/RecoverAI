from pydantic import BaseModel, Field
from typing import Optional

class PolicyConfigSchema(BaseModel):
    MAX_RETRIES: int = Field(..., ge=1, le=10, description="Maximum automated retry attempts allowed")
    MAX_REMINDERS: int = Field(..., ge=1, le=10, description="Maximum customer reminder communications allowed")
    MIN_RECOVERY_PROBABILITY: float = Field(..., ge=0.01, le=1.0, description="Minimum recovery probability required for automated execution")
    HITL_AMOUNT_THRESHOLD: float = Field(..., ge=1000.0, description="Amount in INR above which transactions require human approval")
    HITL_CONFIDENCE_THRESHOLD: float = Field(..., ge=0.1, le=1.0, description="Diagnosis confidence score below which human review is required")
    HITL_FAILED_ATTEMPTS_THRESHOLD: int = Field(..., ge=1, le=10, description="Number of failed attempts before escalating to human review")
    SIMULATION_MODE: bool = Field(True, description="Enable deterministic simulation mode")

class UpdatePolicyConfigRequest(BaseModel):
    MAX_RETRIES: Optional[int] = Field(None, ge=1, le=10)
    MAX_REMINDERS: Optional[int] = Field(None, ge=1, le=10)
    MIN_RECOVERY_PROBABILITY: Optional[float] = Field(None, ge=0.01, le=1.0)
    HITL_AMOUNT_THRESHOLD: Optional[float] = Field(None, ge=1000.0)
    HITL_CONFIDENCE_THRESHOLD: Optional[float] = Field(None, ge=0.1, le=1.0)
    HITL_FAILED_ATTEMPTS_THRESHOLD: Optional[int] = Field(None, ge=1, le=10)
    SIMULATION_MODE: Optional[bool] = None
