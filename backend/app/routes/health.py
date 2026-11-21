"""
Health check endpoints for application and database connectivity.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Response, status
from app.config import settings
from app.database import check_database_connection

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Application Health Check",
    response_description="Returns overall service health and metadata",
)
def get_application_health() -> Dict[str, Any]:
    """
    Returns general application health, version, environment, and server UTC timestamp.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/database",
    summary="Database Connectivity Check",
    response_description="Returns honest database connection status or not_configured",
)
def get_database_health(response: Response) -> Dict[str, Any]:
    """
    Checks MongoDB connectivity when configured.
    - If MONGODB_URI is empty/unset: returns status 'not_configured'.
    - If connected successfully: returns status 'connected'.
    - If connection fails or times out: returns status 'error' with HTTP 503.
    """
    db_status = check_database_connection()

    # If an actual connection error occurred when configured, set HTTP 503
    if db_status.get("status") == "error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return db_status
