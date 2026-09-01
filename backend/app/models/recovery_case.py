import enum
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class RecoveryCaseStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    RECOVERED = "RECOVERED"
    STOPPED = "STOPPED"
    ESCALATED = "ESCALATED"
    FAILED = "FAILED"
    SCHEDULED = "SCHEDULED"

class RecoveryStrategy(str, enum.Enum):
    SMART_RETRY = "SMART_RETRY"
    WAIT_AND_RETRY = "WAIT_AND_RETRY"
    SEND_REMINDER = "SEND_REMINDER"
    SEND_PAYMENT_LINK = "SEND_PAYMENT_LINK"
    OFFER_ALTERNATIVE_PAYMENT_METHOD = "OFFER_ALTERNATIVE_PAYMENT_METHOD"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    STOP_RECOVERY = "STOP_RECOVERY"

class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    case_id = Column(String(50), primary_key=True, index=True)
    payment_id = Column(String(50), ForeignKey("payments.payment_id"), nullable=False)
    batch_id = Column(String(50), nullable=True)
    status = Column(String(50), default=RecoveryCaseStatus.PENDING.value, nullable=False)
    current_strategy = Column(String(50), nullable=True)
    recovery_probability = Column(Float, default=0.0)
    expected_recovery_value = Column(Float, default=0.0)
    estimated_action_cost = Column(Float, default=0.0)
    requires_human_approval = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)
    explanation_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payment = relationship("Payment", back_populates="recovery_cases")
    actions = relationship("RecoveryAction", back_populates="recovery_case", cascade="all, delete-orphan")
    approvals = relationship("HumanApproval", back_populates="recovery_case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="recovery_case", cascade="all, delete-orphan")
