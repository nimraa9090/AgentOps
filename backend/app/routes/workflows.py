"""
Workflow management routes for AgentOps — Abyssal Intelligence.
Provides CRUD API endpoints under /api/v1/workflows.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.database import get_database
from app.models.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowStatus,
    WorkflowUpdate,
)
from app.repositories.workflow_repository import (
    DuplicateWorkflowNameError,
    WorkflowRepository,
    WorkflowRepositoryError,
)

logger = logging.getLogger("agentops.routes.workflows")

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def get_workflow_repository() -> WorkflowRepository:
    """
    FastAPI dependency injecting an initialized WorkflowRepository instance.
    Raises HTTP 503 if the database is disconnected or unconfigured.
    """
    db = get_database()
    if db is None:
        logger.error("Failed to inject WorkflowRepository: MongoDB is not connected.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Ensure MongoDB Atlas is connected.",
        )
    return WorkflowRepository(db=db)


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Workflow",
    description="Registers a new autonomous subsea workflow with validated steps and default status.",
)
def create_workflow(
    workflow_in: WorkflowCreate,
    repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowResponse:
    """
    Creates a new workflow in MongoDB.
    
    - Returns 201 Created with the serialized WorkflowResponse.
    - Returns 409 Conflict if a workflow with the same name already exists.
    - Returns 422 Unprocessable Entity for invalid request payloads.
    """
    try:
        created_wf = repo.create_workflow(workflow_in)
        logger.info("Successfully registered workflow '%s' (id: %s)", created_wf.name, created_wf.id)
        return created_wf
    except DuplicateWorkflowNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except WorkflowRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(exc)}",
        ) from exc


@router.get(
    "",
    response_model=List[WorkflowResponse],
    status_code=status.HTTP_200_OK,
    summary="List Workflows",
    description="Retrieves a paginated list of workflows with optional status filtering. Sets X-Total-Count header.",
)
def list_workflows(
    response: Response,
    skip: int = Query(default=0, ge=0, description="Offset: number of records to skip"),
    limit: int = Query(default=50, ge=1, le=100, description="Page size: maximum records to return"),
    status: Optional[WorkflowStatus] = Query(default=None, description="Filter by workflow status"),
    repo: WorkflowRepository = Depends(get_workflow_repository),
) -> List[WorkflowResponse]:
    """
    Fetches paginated workflows from MongoDB with optional status filtering.
    
    - Returns 200 OK with list of WorkflowResponse items.
    - Populates 'X-Total-Count' header with total matching records.
    """
    try:
        workflows, total_count = repo.get_all_workflows(skip=skip, limit=limit, status=status)
        response.headers["X-Total-Count"] = str(total_count)
        return workflows
    except WorkflowRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch workflows: {str(exc)}",
        ) from exc


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Workflow by ID",
    description="Retrieves a single workflow by its unique identifier or ObjectId.",
)
def get_workflow(
    workflow_id: str,
    repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowResponse:
    """
    Retrieves a workflow by ID.
    
    - Returns 200 OK with WorkflowResponse.
    - Returns 404 Not Found if no workflow matches the supplied ID.
    """
    try:
        wf = repo.get_workflow_by_id(workflow_id)
        if not wf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow with ID '{workflow_id}' was not found.",
            )
        return wf
    except HTTPException:
        raise
    except WorkflowRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving workflow: {str(exc)}",
        ) from exc


@router.patch(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Workflow",
    description="Applies partial updates to an existing workflow.",
)
def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowResponse:
    """
    Updates a workflow with partial fields.
    
    - Returns 200 OK with updated WorkflowResponse.
    - Returns 404 Not Found if the workflow does not exist.
    - Returns 409 Conflict if updating name conflicts with an existing workflow.
    """
    try:
        updated = repo.update_workflow(workflow_id, workflow_update)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow with ID '{workflow_id}' was not found.",
            )
        logger.info("Updated workflow '%s' (id: %s)", updated.name, workflow_id)
        return updated
    except DuplicateWorkflowNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except WorkflowRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating workflow: {str(exc)}",
        ) from exc


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Workflow",
    description="Deletes a workflow from MongoDB.",
)
def delete_workflow(
    workflow_id: str,
    repo: WorkflowRepository = Depends(get_workflow_repository),
) -> Response:
    """
    Deletes a workflow by ID.
    
    - Returns 204 No Content on successful deletion.
    - Returns 404 Not Found if the workflow does not exist.
    """
    try:
        deleted = repo.delete_workflow(workflow_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow with ID '{workflow_id}' was not found.",
            )
        logger.info("Deleted workflow with id: %s", workflow_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except WorkflowRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting workflow: {str(exc)}",
        ) from exc
