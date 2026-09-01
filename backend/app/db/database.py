from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase
from app.config import settings

# Determine connect args (SQLite needs check_same_thread=False for FastAPI)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create engine
engine = create_engine(
    settings.DATABASE_URL, connect_args=connect_args
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modern SQLAlchemy 2.0 Base class
class Base(DeclarativeBase):
    pass

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
