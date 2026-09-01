from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.customer_analysis import CustomerAnalysisResult
from app.schemas.strategy import StrategyResult
from app.schemas.policy import PolicyResultSchema

class ActionResultSchema(BaseModel):
    action: str
    result: str
    recovered_amount: float

class RecoveryResult(BaseModel):
    case_id: str
    status: str
    diagnosis: DiagnosisResult
    customer_analysis: CustomerAnalysisResult
    strategy: StrategyResult
    policy: PolicyResultSchema
    action_result: Optional[ActionResultSchema] = None
    explanation: Optional[dict] = None
