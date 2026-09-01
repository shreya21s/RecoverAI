from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.schemas.policy import PolicyResultSchema
from app.schemas.recovery_result import ActionResultSchema

class AgentTraceEvent(BaseModel):
    step: str
    status: str
    summary: str
    triggered_rules: Optional[List[str]] = None
    timestamp: str

class GraphRunResultSchema(BaseModel):
    case_id: str
    workflow_status: str
    diagnosis: Optional[Dict[str, Any]] = None
    customer_analysis: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    policy: Optional[PolicyResultSchema] = None
    action_result: Optional[ActionResultSchema] = None
    explanation: Optional[Dict[str, Any]] = None
    final_status: str
    agent_trace: List[AgentTraceEvent]
    errors: List[str] = Field(default=[])
