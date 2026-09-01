from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    payment_method = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    failure_code = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    retry_count = Column(Integer, default=0)
    reminder_count = Column(Integer, default=0)
    is_disputed = Column(Boolean, default=False)
    is_recovered = Column(Boolean, default=False)

    # Relationships
    customer = relationship("Customer", back_populates="payments")
    recovery_cases = relationship("RecoveryCase", back_populates="payment", cascade="all, delete-orphan")
