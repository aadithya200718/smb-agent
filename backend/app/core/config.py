"""
Environment configuration using Pydantic Settings.

Loads settings from a .env file and validates required fields.
All secrets and connection strings should be set via environment variables.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the project root (backend/) so .env is found regardless of cwd
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ──────────────────────────────────────────────────────────
    ENVIRONMENT: str = Field(default="development", description="Runtime environment")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    HOST: str = Field(default="0.0.0.0", description="Server bind address")
    PORT: int = Field(default=8000, description="Server port")

    # ── MongoDB ─────────────────────────────────────────────────────────
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string",
    )
    MONGODB_DB_NAME: str = Field(
        default="whatsapp_business_agent",
        description="Database name",
    )
    MONGODB_MIN_POOL_SIZE: int = Field(default=5, description="Min connection pool size")
    MONGODB_MAX_POOL_SIZE: int = Field(default=50, description="Max connection pool size")

    # ── Qdrant Vector Database ──────────────────────────────────────────
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL",
    )
    QDRANT_API_KEY: Optional[str] = Field(
        default=None,
        description="Qdrant API key (required for cloud)",
    )
    QDRANT_COLLECTION_NAME: str = Field(
        default="business_memory",
        description="Default vector collection name",
    )
    QDRANT_VECTOR_SIZE: int = Field(
        default=384,
        description="Embedding vector dimension",
    )

    # ── API Keys (used in later phases) ─────────────────────────────────
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")
    TWILIO_ACCOUNT_SID: Optional[str] = Field(default=None, description="Twilio account SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default=None, description="Twilio auth token")
    TWILIO_WHATSAPP_NUMBER: Optional[str] = Field(default=None, description="Twilio WhatsApp Sandbox Number")
    WEBHOOK_BASE_URL: Optional[str] = Field(default=None, description="Base URL for webhooks")
    RAZORPAY_KEY_ID: Optional[str] = Field(default=None, description="Razorpay key ID")
    RAZORPAY_KEY_SECRET: Optional[str] = Field(default=None, description="Razorpay key secret")
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Razorpay webhook signing secret")

    # ── Petpooja POS ───────────────────────────────────────────────────
    PETPOOJA_API_TOKEN: Optional[str] = Field(default=None, description="Petpooja POS API token")
    PETPOOJA_RESTAURANT_ID: Optional[str] = Field(default=None, description="Petpooja Restaurant ID")

    # ── Security / JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="JWT signing secret",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_MINUTES: int = Field(default=1440, description="JWT token TTL in minutes")

    # ── Validators ──────────────────────────────────────────────────────
    @field_validator("MONGODB_URI")
    @classmethod
    def validate_mongodb_uri(cls, v: str) -> str:
        """Ensure the MongoDB URI starts with a recognised scheme."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MONGODB_URI must start with 'mongodb://' or 'mongodb+srv://'")
        return v

    @field_validator("QDRANT_URL")
    @classmethod
    def validate_qdrant_url(cls, v: str) -> str:
        """Ensure the Qdrant URL starts with http(s)."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("QDRANT_URL must start with 'http://' or 'https://'")
        return v

    @property
    def is_production(self) -> bool:
        """Return True when running in production."""
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()
