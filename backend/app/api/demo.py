from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.data.seed_data import reset_demo_data

router = APIRouter(prefix="/api/demo", tags=["demo"])

@router.post("/reset")
def reset_database(db: Session = Depends(get_db)):
    try:
        reset_demo_data(db)
        return {
            "status": "success",
            "message": "Database reset and seeded with 100 cases"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database reset failed: {str(e)}")
