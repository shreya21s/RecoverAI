import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.approval import HumanApproval
from app.models.audit_log import AuditLog
from app.data.generator import generate_synthetic_data

logger = logging.getLogger("recoverai.seeder")

def seed_demo_data(db: Session):
    """
    Seeds the database with deterministic demo data if tables are empty.
    """
    # Check if data already exists to prevent duplicate seeding
    if db.query(RecoveryCase).first() is not None:
        logger.info("Demo data already seeded. Skipping initial seeding.")
        return False

    logger.info("Starting database seeding...")

    customers_data, payments_data, cases_data = generate_synthetic_data()

    # 1. Insert Customers
    for cust in customers_data:
        db_cust = Customer(**cust)
        db.add(db_cust)
    
    # Commit customers so payments FKs are valid
    db.commit()

    # 2. Insert Payments
    for pay in payments_data:
        db_pay = Payment(**pay)
        db.add(db_pay)

    # Commit payments so recovery cases FKs are valid
    db.commit()

    # 3. Insert Recovery Cases
    for case in cases_data:
        db_case = RecoveryCase(**case)
        db.add(db_case)

    db.commit()
    logger.info("Database seeding successfully completed.")
    return True

def reset_demo_data(db: Session):
    """
    Deletes all records from the database and runs the seeder again.
    """
    logger.info("Resetting demo data...")

    from app.db.database import engine, Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    logger.info("Tables re-created successfully. Re-seeding database...")
    return seed_demo_data(db)
