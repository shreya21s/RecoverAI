import enum
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class ApprovalDecision(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"

class HumanApproval(Base):
    __tablename__ = "human_approvals"

    approval_id = Column(String(50), primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("recovery_cases.case_id"), nullable=False)
    reviewer = Column(String(100), nullable=True)
    decision = Column(String(50), default=ApprovalDecision.PENDING.value, nullable=False)
    override_action = Column(String(50), nullable=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="approvals")
