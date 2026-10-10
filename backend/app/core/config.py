from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "OpsPulse AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "opspulse_ai_dev_jwt_secret_key_9923847192384791823749812739481"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # PostgreSQL Database URL
    DATABASE_URL: str = "postgresql://postgres@localhost:5433/opspulse"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Operational configuration
    DEFAULT_ACK_TIMEOUT_SECONDS: int = 300
    ALERT_CORRELATION_WINDOW_MINUTES: int = 15
    ESCALATION_CHECK_INTERVAL_SECONDS: int = 10

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
