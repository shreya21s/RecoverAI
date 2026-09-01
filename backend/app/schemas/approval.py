from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.schemas.policy import PolicyResultSchema
from app.schemas.recovery_result import ActionResultSchema

class HumanDecisionRequest(BaseModel):
    reviewer_id: str = Field(..., description="ID of the human reviewer")
    reason: Optional[str] = Field(default=None, description="Reason for the decision")

class PendingApprovalSchema(BaseModel):
    case_id: str
    payment_amount: float
    recommended_action: str
    recovery_probability: float
    triggered_rules: List[str]
    created_at: str
    explanation_json: Optional[Dict[str, Any]] = None

class ApprovalContextSchema(BaseModel):
    case_id: str
    payment: Dict[str, Any]
    customer_analysis: Dict[str, Any]
    diagnosis: Dict[str, Any]
    strategy: Dict[str, Any]
    policy: Dict[str, Any]
    explanation_json: Optional[Dict[str, Any]] = None

class HumanDecisionResponse(BaseModel):
    decision: str
    reviewer_id: str
    reason: Optional[str] = None

class PolicyRevalidationResponse(BaseModel):
    decision: str
    action_allowed: bool

class ApprovalResponseSchema(BaseModel):
    case_id: str
    human_decision: HumanDecisionResponse
    policy_revalidation: PolicyRevalidationResponse
    action_result: Optional[ActionResultSchema] = None
    final_status: str
