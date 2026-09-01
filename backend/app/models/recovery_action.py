from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    action_id = Column(String(50), primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("recovery_cases.case_id"), nullable=False)
    action_type = Column(String(50), nullable=False) # e.g. SMART_RETRY, SEND_REMINDER
    status = Column(String(50), nullable=False) # e.g. REQUESTED, VALIDATED, DISPATCHED, PROCESSING, SUCCEEDED, FAILED, BLOCKED, CANCELLED
    result = Column(String(255), nullable=True)
    recovered_amount = Column(Float, default=0.0)
    executed_at = Column(DateTime, nullable=True)
    
    # Extended execution request fields
    attempt_number = Column(Integer, default=1, nullable=False)
    idempotency_key = Column(String(100), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    simulation_mode = Column(Boolean, default=True)
    execution_context = Column(JSON, nullable=True)
    policy_decision = Column(String(50), nullable=True)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="actions")
