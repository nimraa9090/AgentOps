"""
Agent management routes for AgentOps — Abyssal Intelligence.
Provides CRUD API endpoints under /api/v1/agents.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.database import get_database
from app.models.agent import (
    AgentCreate,
    AgentResponse,
    AgentStatus,
    AgentUpdate,
)
from app.repositories.agent_repository import (
    AgentRepository,
    AgentRepositoryError,
    DuplicateAgentNameError,
)

logger = logging.getLogger("agentops.routes.agents")

router = APIRouter(prefix="/agents", tags=["Agents"])


def get_agent_repository() -> AgentRepository:
    """
    FastAPI dependency injecting an initialized AgentRepository instance.
    Raises HTTP 503 if the database is disconnected or unconfigured.
    """
    db = get_database()
    if db is None:
        logger.error("Failed to inject AgentRepository: MongoDB is not connected.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Ensure MongoDB Atlas is connected.",
        )
    return AgentRepository(db=db)


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Subsea Agent",
    description="Registers a new autonomous subsea agent with validated configuration and default metrics.",
)
def create_agent(
    agent_in: AgentCreate,
    repo: AgentRepository = Depends(get_agent_repository),
) -> AgentResponse:
    """
    Creates a new agent in MongoDB.
    
    - Returns 201 Created with the serialized AgentResponse.
    - Returns 409 Conflict if an agent with the same name already exists.
    - Returns 422 Unprocessable Entity for invalid request payloads.
    """
    try:
        created_agent = repo.create_agent(agent_in)
        logger.info("Successfully registered agent '%s' (id: %s)", created_agent.name, created_agent.id)
        return created_agent
    except DuplicateAgentNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except AgentRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(exc)}",
        ) from exc


@router.get(
    "",
    response_model=List[AgentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Subsea Agents",
    description="Retrieves a paginated list of subsea agents with optional status filtering. Sets X-Total-Count header.",
)
def list_agents(
    response: Response,
    skip: int = Query(default=0, ge=0, description="Offset: number of records to skip"),
    limit: int = Query(default=50, ge=1, le=100, description="Page size: maximum records to return"),
    status: Optional[AgentStatus] = Query(default=None, description="Filter by operational status"),
    repo: AgentRepository = Depends(get_agent_repository),
) -> List[AgentResponse]:
    """
    Fetches paginated agents from MongoDB with optional status filtering.
    
    - Returns 200 OK with list of AgentResponse items.
    - Populates 'X-Total-Count' header with total matching records.
    """
    try:
        agents, total_count = repo.get_all_agents(skip=skip, limit=limit, status=status)
        response.headers["X-Total-Count"] = str(total_count)
        return agents
    except AgentRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agents: {str(exc)}",
        ) from exc


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Subsea Agent by ID",
    description="Retrieves a single subsea agent by its unique identifier or ObjectId.",
)
def get_agent(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repository),
) -> AgentResponse:
    """
    Retrieves an agent by ID.
    
    - Returns 200 OK with AgentResponse.
    - Returns 404 Not Found if no agent matches the supplied ID.
    """
    try:
        agent = repo.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID '{agent_id}' was not found.",
            )
        return agent
    except HTTPException:
        raise
    except AgentRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent: {str(exc)}",
        ) from exc


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Subsea Agent",
    description="Applies partial updates to an existing subsea agent.",
)
def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    repo: AgentRepository = Depends(get_agent_repository),
) -> AgentResponse:
    """
    Updates an agent with partial fields.
    
    - Returns 200 OK with updated AgentResponse.
    - Returns 404 Not Found if the agent does not exist.
    - Returns 409 Conflict if updating name conflicts with an existing agent.
    """
    try:
        updated = repo.update_agent(agent_id, agent_update)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID '{agent_id}' was not found.",
            )
        logger.info("Updated agent '%s' (id: %s)", updated.name, agent_id)
        return updated
    except DuplicateAgentNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except AgentRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent: {str(exc)}",
        ) from exc


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Subsea Agent",
    description="Deletes a subsea agent from MongoDB.",
)
def delete_agent(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repository),
) -> Response:
    """
    Deletes an agent by ID.
    
    - Returns 204 No Content on successful deletion.
    - Returns 404 Not Found if the agent does not exist.
    """
    try:
        deleted = repo.delete_agent(agent_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID '{agent_id}' was not found.",
            )
        logger.info("Deleted agent with id: %s", agent_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except AgentRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting agent: {str(exc)}",
        ) from exc
