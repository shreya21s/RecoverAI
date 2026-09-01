from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.schemas.common import BaseSchema

class CustomerBase(BaseModel):
    name: str = Field(..., max_length=255)
    segment: Optional[str] = Field(None, max_length=50)
    lifetime_value: float = 0.0
    total_successful_payments: int = 0
    total_failed_payments: int = 0
    average_payment_amount: float = 0.0
    engagement_score: float = 0.0

class CustomerCreate(CustomerBase):
    customer_id: str = Field(..., max_length=50)

class Customer(CustomerBase, BaseSchema):
    customer_id: str
    created_at: datetime
    updated_at: datetime
