"""
Application configuration management using pydantic-settings.
Loads settings from environment variables and the local .env file.
"""

from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # Application Info
    PROJECT_NAME: str = "AgentOps API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server Bind Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Allowed Origins
    # Defaults to local Next.js frontend at http://localhost:3000
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    # MongoDB Configuration
    # Defaults to None so if unconfigured, it can be reported honestly as 'not_configured'
    MONGODB_URI: Optional[str] = Field(default=None)
    DATABASE_NAME: str = "agentops_abyssal"

    # Security & JWT Configuration
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """
        Supports parsing either a JSON list or a comma-separated string of origins.
        """
        if isinstance(value, str):
            # If comma-separated, split into a clean list of origins
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        elif isinstance(value, list):
            return value
        return ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings singleton instance
settings = Settings()
