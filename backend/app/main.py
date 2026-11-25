"""
AgentOps — Abyssal Intelligence Backend API
Main FastAPI entry point with CORS and health routes.
"""

from contextlib import asynccontextmanager
import logging
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import close_database_connection, get_database
from app.repositories.agent_repository import init_agent_indexes
from app.repositories.workflow_repository import init_workflow_indexes
from app.repositories.execution_repository import init_execution_indexes
from app.routes.health import router as health_router
from app.routes.agents import router as agents_router
from app.routes.workflows import router as workflows_router

# Setup safe structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agentops.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and graceful shutdown tasks.
    """
    # Safe startup diagnostic logging without exposing sensitive secrets
    db_summary = settings.get_safe_db_summary()
    logger.info("Initializing %s (v%s) in '%s' environment", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT)
    logger.info(
        "Database configuration loaded: is_configured=%s, scheme='%s', database='%s', env_file_found=%s",
        db_summary["is_configured"],
        db_summary["scheme"],
        db_summary["database_name"],
        db_summary["env_file_found"],
    )

    # Initialize database indexes safely if database is connected
    try:
        db = get_database()
        if db is not None:
            agent_indexes = init_agent_indexes(db)
            logger.info("MongoDB indexes verified for 'agents' collection: %s", agent_indexes)
            wf_indexes = init_workflow_indexes(db)
            logger.info("MongoDB indexes verified for 'workflows' collection: %s", wf_indexes)
            exec_indexes = init_execution_indexes(db)
            logger.info("MongoDB indexes verified for 'executions' collection: %s", exec_indexes)
        else:
            logger.warning("MongoDB not configured; skipping index initialization.")
    except Exception as exc:
        logger.warning("MongoDB index initialization skipped: %s", str(exc))

    yield

    # Shutdown: Cleanly close database connection pool
    logger.info("Shutting down %s, closing database connections...", settings.PROJECT_NAME)
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
app.include_router(agents_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")


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
