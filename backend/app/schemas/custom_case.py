from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.graph_run import GraphRunResultSchema

class CreateCustomCaseRequest(BaseModel):
    # Payment / Revenue Details
    amount: float = Field(..., gt=0, description="Personalized revenue amount in INR")
    currency: str = Field("INR", max_length=3)
    payment_method: str = Field("UPI", max_length=50)
    failure_code: str = Field("TEMPORARY_BANK_FAILURE", max_length=100)
    retry_count: int = Field(0, ge=0)
    reminder_count: int = Field(0, ge=0)
    is_disputed: bool = Field(False)
    
    # Customer Details
    customer_name: Optional[str] = Field("Custom Customer", max_length=255)
    customer_segment: Optional[str] = Field("RELIABLE", max_length=50)
    customer_ltv: Optional[float] = Field(50000.0, ge=0.0)
    successful_payments: Optional[int] = Field(10, ge=0)
    failed_payments: Optional[int] = Field(1, ge=0)
    average_payment_amount: Optional[float] = Field(None, ge=0.0)
    engagement_score: Optional[float] = Field(8.0, ge=0.0, le=10.0)
    
    # Execution Settings
    auto_run: bool = Field(True, description="Immediately trigger multi-agent recovery workflow")

class CreateCustomCaseResponse(BaseModel):
    case_id: str
    payment_id: str
    customer_id: str
    status: str
    amount: float
    currency: str
    message: str
    graph_result: Optional[GraphRunResultSchema] = None
