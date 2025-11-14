"""Application configuration using Pydantic Settings."""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="DEBUG")
    SECRET_KEY: str = Field(default="your-secret-key-here-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://trading_user:trading_password@localhost:5432/trading_db",
        description="PostgreSQL database connection URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # API Keys
    TWELVE_DATA_API_KEY: Optional[str] = Field(
        default=None,
        description="Twelve Data API key for market data"
    )

    # Interactive Brokers (Phase 5)
    IBKR_USERNAME: Optional[str] = Field(default=None)
    IBKR_PASSWORD: Optional[str] = Field(default=None)
    IBKR_TRADING_MODE: str = Field(default="paper")
    IBKR_PORT: int = Field(default=7497)

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    def validate_required_keys(self, phase: str = "development") -> None:
        """
        Validate required API keys based on deployment phase.

        Args:
            phase: Deployment phase (development, production, etc.)

        Raises:
            ValueError: If required keys are missing
        """
        missing_keys = []

        # Twelve Data API is required for market data
        if not self.TWELVE_DATA_API_KEY:
            missing_keys.append("TWELVE_DATA_API_KEY")

        # IBKR credentials only required in production/Phase 5
        if phase == "production":
            if not self.IBKR_USERNAME:
                missing_keys.append("IBKR_USERNAME")
            if not self.IBKR_PASSWORD:
                missing_keys.append("IBKR_PASSWORD")

        if missing_keys:
            raise ValueError(
                f"Missing required API keys for {phase}: {', '.join(missing_keys)}. "
                f"Please set these in your .env file."
            )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() in ["development", "dev"]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() in ["production", "prod"]


# Create global settings instance
settings = Settings()
