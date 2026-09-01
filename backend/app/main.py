from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, demo, cases, approvals, batches, audit
from app.db.init_db import init_db
from app.db.database import SessionLocal
from app.data.seed_data import seed_demo_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    init_db()
    # Seed default demo data if not already present
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield

app = FastAPI(title="RecoverAI API", lifespan=lifespan)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(demo.router)
app.include_router(cases.router)
app.include_router(approvals.router)
app.include_router(batches.router)
app.include_router(audit.router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "RecoverAI API is running"
    }
