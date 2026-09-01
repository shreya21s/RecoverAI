import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite:///./recoverai.db")
    DEMO_MODE: bool = Field(default=True)
    SIMULATION_MODE: bool = Field(default=True)
    AI_PROVIDER: Optional[str] = Field(default=None)
    AI_MODEL: Optional[str] = Field(default=None)
    AI_API_KEY: Optional[str] = Field(default=None)

    # Configurable Policy Thresholds
    MAX_RETRIES: int = Field(default=3)
    MAX_REMINDERS: int = Field(default=3)
    MIN_RECOVERY_PROBABILITY: float = Field(default=0.15)
    HITL_AMOUNT_THRESHOLD: float = Field(default=50000.0)
    HITL_CONFIDENCE_THRESHOLD: float = Field(default=0.70)
    HITL_FAILED_ATTEMPTS_THRESHOLD: int = Field(default=2)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Global settings instance
settings = Settings()
