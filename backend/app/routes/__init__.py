"""
Routes package for AgentOps API
"""

from app.routes.health import router as health_router
from app.routes.agents import router as agents_router
from app.routes.workflows import router as workflows_router

__all__ = ["health_router", "agents_router", "workflows_router"]
