from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.schemas.common import BaseSchema

class PaymentBase(BaseModel):
    customer_id: str = Field(..., max_length=50)
    amount: float
    currency: str = Field(..., min_length=3, max_length=3)
    payment_method: str = Field(..., max_length=50)
    status: str = Field(..., max_length=50)
    failure_code: Optional[str] = Field(None, max_length=100)
    retry_count: int = 0
    reminder_count: int = 0
    is_disputed: bool = False
    is_recovered: bool = False

class PaymentCreate(PaymentBase):
    payment_id: str = Field(..., max_length=50)

class Payment(PaymentBase, BaseSchema):
    payment_id: str
    created_at: datetime
