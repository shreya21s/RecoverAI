import enum
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class BatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"

class RecoveryBatch(Base):
    __tablename__ = "recovery_batches"

    batch_id = Column(String(50), primary_key=True, index=True)
    batch_name = Column(String(100), nullable=False)
    status = Column(String(50), default=BatchStatus.PENDING.value, nullable=False)
    
    # Aggregated metrics
    total_cases = Column(Integer, default=0)
    processed_cases = Column(Integer, default=0)
    approved_cases = Column(Integer, default=0)
    recovered_cases = Column(Integer, default=0)
    stopped_cases = Column(Integer, default=0)
    blocked_cases = Column(Integer, default=0)
    hitl_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    
    # New aggregated metrics for Part 11
    ai_recommended_cases = Column(Integer, default=0)
    scheduled_cases = Column(Integer, default=0)
    executed_cases = Column(Integer, default=0)
    
    total_outstanding_amount = Column(Float, default=0.0)
    total_recovered_amount = Column(Float, default=0.0)
    total_expected_recovery_value = Column(Float, default=0.0)
    recovery_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    cases = relationship("RecoveryBatchItem", back_populates="batch", cascade="all, delete-orphan")


class RecoveryBatchItem(Base):
    __tablename__ = "recovery_batch_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), ForeignKey("recovery_batches.batch_id"), nullable=False)
    case_id = Column(String(50), ForeignKey("recovery_cases.case_id"), nullable=False)
    processing_status = Column(String(50), default="PENDING", nullable=False) # PENDING, COMPLETED, FAILED
    final_status = Column(String(50), nullable=True)
    recovered_amount = Column(Float, default=0.0)
    error_message = Column(String(255), nullable=True)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    batch = relationship("RecoveryBatch", back_populates="cases")
