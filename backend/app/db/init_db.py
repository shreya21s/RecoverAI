from app.db.database import engine, Base
# Import all models to ensure they are registered on the Base metadata
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.approval import HumanApproval
from app.models.audit_log import AuditLog
from app.models.batch import RecoveryBatch, RecoveryBatchItem

def init_db():
    Base.metadata.create_all(bind=engine)
