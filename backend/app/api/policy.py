from fastapi import APIRouter, HTTPException
from app.config import settings
from app.schemas.policy_config import PolicyConfigSchema, UpdatePolicyConfigRequest

router = APIRouter(prefix="/api/policy", tags=["policy"])

# Default baseline configuration constants
DEFAULT_CONFIG = {
    "MAX_RETRIES": 3,
    "MAX_REMINDERS": 3,
    "MIN_RECOVERY_PROBABILITY": 0.15,
    "HITL_AMOUNT_THRESHOLD": 50000.0,
    "HITL_CONFIDENCE_THRESHOLD": 0.70,
    "HITL_FAILED_ATTEMPTS_THRESHOLD": 2,
    "SIMULATION_MODE": True,
}

@router.get("/config", response_model=PolicyConfigSchema)
def get_policy_config():
    """
    Returns the current dynamic policy engine configuration thresholds.
    """
    return PolicyConfigSchema(
        MAX_RETRIES=settings.MAX_RETRIES,
        MAX_REMINDERS=settings.MAX_REMINDERS,
        MIN_RECOVERY_PROBABILITY=settings.MIN_RECOVERY_PROBABILITY,
        HITL_AMOUNT_THRESHOLD=settings.HITL_AMOUNT_THRESHOLD,
        HITL_CONFIDENCE_THRESHOLD=settings.HITL_CONFIDENCE_THRESHOLD,
        HITL_FAILED_ATTEMPTS_THRESHOLD=settings.HITL_FAILED_ATTEMPTS_THRESHOLD,
        SIMULATION_MODE=settings.SIMULATION_MODE,
    )

@router.put("/config", response_model=PolicyConfigSchema)
def update_policy_config(payload: UpdatePolicyConfigRequest):
    """
    Updates the active policy engine thresholds dynamically.
    """
    try:
        if payload.MAX_RETRIES is not None:
            settings.MAX_RETRIES = payload.MAX_RETRIES
        if payload.MAX_REMINDERS is not None:
            settings.MAX_REMINDERS = payload.MAX_REMINDERS
        if payload.MIN_RECOVERY_PROBABILITY is not None:
            settings.MIN_RECOVERY_PROBABILITY = payload.MIN_RECOVERY_PROBABILITY
        if payload.HITL_AMOUNT_THRESHOLD is not None:
            settings.HITL_AMOUNT_THRESHOLD = payload.HITL_AMOUNT_THRESHOLD
        if payload.HITL_CONFIDENCE_THRESHOLD is not None:
            settings.HITL_CONFIDENCE_THRESHOLD = payload.HITL_CONFIDENCE_THRESHOLD
        if payload.HITL_FAILED_ATTEMPTS_THRESHOLD is not None:
            settings.HITL_FAILED_ATTEMPTS_THRESHOLD = payload.HITL_FAILED_ATTEMPTS_THRESHOLD
        if payload.SIMULATION_MODE is not None:
            settings.SIMULATION_MODE = payload.SIMULATION_MODE

        return get_policy_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy config: {str(e)}")

@router.post("/reset", response_model=PolicyConfigSchema)
def reset_policy_config():
    """
    Resets all policy thresholds back to system default values.
    """
    for key, value in DEFAULT_CONFIG.items():
        setattr(settings, key, value)
    return get_policy_config()
