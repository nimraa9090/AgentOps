"""
AgentOps — Abyssal Intelligence Backend API
Main FastAPI entry point with CORS and health routes.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import close_database_connection
from app.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and graceful shutdown tasks.
    """
    # Startup: App initialization
    yield
    # Shutdown: Cleanly close database connection pool
    close_database_connection()


# Initialize FastAPI application titled 'AgentOps API'
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AgentOps — Abyssal Intelligence operations and telemetry",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local Next.js frontend at http://localhost:3000 (and any other configured origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(health_router, prefix="/api/v1")


@app.get(
    "/",
    tags=["Root"],
    summary="Root Service Info",
    response_description="Returns API name and operational status",
)
def read_root() -> Dict[str, Any]:
    """
    Root endpoint confirming service identity and status.
    """
    return {
        "name": settings.PROJECT_NAME,
        "status": "running",
        "version": settings.VERSION,
        "documentation": "/docs",
    }
