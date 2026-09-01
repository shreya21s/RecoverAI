from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.schemas.recovery_result import ActionResultSchema

class BatchCreateRequest(BaseModel):
    batch_name: str
    case_ids: Optional[List[str]] = Field(default=None, description="Optional explicit case IDs. If omitted, selects eligible cases.")

class BatchCaseItemSchema(BaseModel):
    case_id: str
    processing_status: str
    final_status: Optional[str] = None
    recovered_amount: float
    error_message: Optional[str] = None

class BatchResponseSchema(BaseModel):
    batch_id: str
    batch_name: str
    status: str
    total_cases: int
    processed_cases: int
    approved_cases: int
    recovered_cases: int
    stopped_cases: int
    blocked_cases: int
    hitl_cases: int
    failed_cases: int
    
    # New fields for Part 11
    ai_recommended_cases: int = 0
    scheduled_cases: int = 0
    executed_cases: int = 0
    
    total_outstanding_amount: float
    total_recovered_amount: float
    total_expected_recovery_value: float
    recovery_rate: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cases: List[BatchCaseItemSchema] = []

class BatchSummarySchema(BaseModel):
    total_cases: int
    processed_cases: int
    recovered_cases: int
    stopped_cases: int
    hitl_cases: int
    failed_cases: int
    ai_recommended_cases: int = 0
    scheduled_cases: int = 0
    executed_cases: int = 0

class BatchFinancialImpactSchema(BaseModel):
    total_outstanding_revenue: float
    eligible_outstanding_revenue: float
    recovered_revenue: float
    expected_recovery_value: float
    unrecovered_revenue: float
    recovery_rate: float

class BatchSafetyMetricsSchema(BaseModel):
    policy_block_rate: float
    hitl_escalation_rate: float

class BatchBaselineComparisonSchema(BaseModel):
    baseline_recovered_revenue: float
    recoverai_recovered_revenue: float
    incremental_revenue: float
    improvement_percentage: float

class BatchImpactReportSchema(BaseModel):
    batch_id: str
    summary: BatchSummarySchema
    financial_impact: BatchFinancialImpactSchema
    safety_metrics: BatchSafetyMetricsSchema
    baseline_comparison: BatchBaselineComparisonSchema
    decision_insights: Optional[Dict[str, Any]] = None
