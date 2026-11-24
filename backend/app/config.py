"""
Application configuration management using pydantic-settings.
Loads settings from environment variables and the backend .env file.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

# Explicitly locate backend directory and .env file
# This prevents relative path mismatches when uvicorn is launched from the project root
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BACKEND_DIR / ".env"

# Load .env into process environment if it exists
if ENV_FILE_PATH.exists():
    load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)

logger = logging.getLogger("agentops.config")


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
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        elif isinstance(value, list):
            return value
        return ["http://localhost:3000"]

    def get_safe_db_summary(self) -> Dict[str, Any]:
        """
        Returns safe diagnostic metadata about MongoDB configuration
        WITHOUT exposing credentials, passwords, or the full URI.
        """
        is_configured = bool(self.MONGODB_URI and self.MONGODB_URI.strip())
        uri_scheme = "none"
        if is_configured and self.MONGODB_URI:
            if "://" in self.MONGODB_URI:
                uri_scheme = self.MONGODB_URI.split("://")[0]
            else:
                uri_scheme = "custom"

        return {
            "is_configured": is_configured,
            "database_name": self.DATABASE_NAME,
            "scheme": uri_scheme,
            "env_file_found": ENV_FILE_PATH.exists(),
            "env_file_path": str(ENV_FILE_PATH),
        }

    model_config = SettingsConfigDict(
        # Check both the explicit backend/.env path and fallback to working directory .env
        env_file=(str(ENV_FILE_PATH), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings singleton instance
settings = Settings()
