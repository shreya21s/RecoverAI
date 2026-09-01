from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    segment = Column(String(50), nullable=True)
    lifetime_value = Column(Float, default=0.0)
    total_successful_payments = Column(Integer, default=0)
    total_failed_payments = Column(Integer, default=0)
    average_payment_amount = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
