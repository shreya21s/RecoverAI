from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String(50), primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("recovery_cases.case_id"), nullable=False)
    batch_id = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    actor_type = Column(String(50), nullable=False) # e.g. SYSTEM, HUMAN
    actor_name = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    decision_summary = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="audit_logs")
