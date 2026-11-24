"""
Workflow repository for AgentOps — Abyssal Intelligence.
Provides data access layer operations for the 'workflows' collection in MongoDB.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, IndexModel, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.database import get_database
from app.models.common import now_utc
from app.models.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowStatus,
    WorkflowUpdate,
)

logger = logging.getLogger("agentops.repositories.workflow")


class WorkflowRepositoryError(Exception):
    """Base exception for workflow repository errors."""
    pass


class DuplicateWorkflowNameError(WorkflowRepositoryError):
    """Raised when attempting to create or rename a workflow with an existing name."""
    pass


class InvalidWorkflowIdError(WorkflowRepositoryError):
    """Raised when an invalid format is supplied for a workflow identifier."""
    pass


def init_workflow_indexes(db: Database) -> List[str]:
    """
    Idempotently initializes indexes on the 'workflows' collection.
    
    Indexes created:
    - idx_workflows_name_unique: Unique constraint on workflow name.
    - idx_workflows_status: Fast lookup by execution status (draft, active, paused, completed, failed).
    - idx_workflows_created_at: Fast chronological sorting for timeline queries.
    
    Returns:
        List of index names created or verified by MongoDB.
    """
    collection: Collection = db["workflows"]
    indexes = [
        IndexModel([("name", ASCENDING)], unique=True, name="idx_workflows_name_unique"),
        IndexModel([("status", ASCENDING)], name="idx_workflows_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_workflows_created_at"),
    ]
    created = collection.create_indexes(indexes)
    logger.info("Ensured indexes on 'workflows' collection: %s", created)
    return created


class WorkflowRepository:
    """
    Repository pattern managing CRUD queries and business data operations
    for the 'workflows' collection in MongoDB.
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initializes repository with database instance.
        If db is not explicitly provided, uses the application global connection.
        """
        self._db = db if db is not None else get_database()
        if self._db is None:
            raise RuntimeError(
                "WorkflowRepository could not obtain a valid database connection. "
                "Ensure MONGODB_URI is properly configured."
            )
        self.collection: Collection = self._db["workflows"]

    @staticmethod
    def _build_id_query(workflow_id: str) -> Dict[str, Any]:
        """
        Constructs a safe query targeting either a BSON ObjectId or a custom string identifier.
        """
        if not workflow_id or not isinstance(workflow_id, str) or not workflow_id.strip():
            raise InvalidWorkflowIdError("Workflow ID must be a non-empty string.")

        clean_id = workflow_id.strip()
        if ObjectId.is_valid(clean_id):
            return {"$or": [{"_id": ObjectId(clean_id)}, {"_id": clean_id}, {"id": clean_id}]}
        return {"$or": [{"_id": clean_id}, {"id": clean_id}]}

    def create_workflow(self, workflow_data: WorkflowCreate) -> WorkflowResponse:
        """
        Inserts a new workflow document into MongoDB.
        
        Args:
            workflow_data: Validated WorkflowCreate model.
            
        Returns:
            WorkflowResponse matching client expectation.
            
        Raises:
            DuplicateWorkflowNameError: If a workflow with the same name already exists.
            WorkflowRepositoryError: For general database insertion failures.
        """
        doc = workflow_data.model_dump(by_alias=True)

        # Attach UTC timestamps
        timestamp = now_utc()
        doc["created_at"] = timestamp
        doc["updated_at"] = timestamp

        try:
            result = self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            return WorkflowResponse.model_validate(doc)
        except DuplicateKeyError as exc:
            logger.warning("Duplicate workflow name rejected: %s", workflow_data.name)
            raise DuplicateWorkflowNameError(
                f"Workflow with name '{workflow_data.name}' already exists."
            ) from exc
        except PyMongoError as exc:
            logger.error("Failed to insert workflow '%s': %s", workflow_data.name, str(exc))
            raise WorkflowRepositoryError(f"Database error creating workflow: {str(exc)}") from exc

    def get_workflow_by_id(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """
        Finds a single workflow by its ObjectId or string ID.
        
        Args:
            workflow_id: String ID or 24-hex ObjectId string.
            
        Returns:
            WorkflowResponse if found, otherwise None.
        """
        try:
            query = self._build_id_query(workflow_id)
        except InvalidWorkflowIdError:
            return None

        try:
            doc = self.collection.find_one(query)
            if not doc:
                return None
            return WorkflowResponse.model_validate(doc)
        except PyMongoError as exc:
            logger.error("Error retrieving workflow '%s': %s", workflow_id, str(exc))
            raise WorkflowRepositoryError(f"Database error retrieving workflow: {str(exc)}") from exc

    def get_all_workflows(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[WorkflowStatus] = None,
    ) -> Tuple[List[WorkflowResponse], int]:
        """
        Retrieves paginated list of workflows and the total count matching filters.
        
        Args:
            skip: Number of documents to skip (offset, >= 0).
            limit: Maximum documents to return (page size, 1 to 100).
            status: Optional WorkflowStatus filter.
            
        Returns:
            Tuple of (list of WorkflowResponse items, total_count).
        """
        query: Dict[str, Any] = {}
        if status is not None:
            query["status"] = status.value if hasattr(status, "value") else str(status)

        safe_skip = max(0, skip)
        safe_limit = max(1, min(100, limit))

        try:
            total_count = self.collection.count_documents(query)
            cursor = (
                self.collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(safe_skip)
                .limit(safe_limit)
            )
            workflows = [WorkflowResponse.model_validate(doc) for doc in cursor]
            return workflows, total_count
        except PyMongoError as exc:
            logger.error("Error querying workflows list: %s", str(exc))
            raise WorkflowRepositoryError(f"Database error fetching workflows: {str(exc)}") from exc

    def update_workflow(
        self,
        workflow_id: str,
        workflow_update: WorkflowUpdate,
    ) -> Optional[WorkflowResponse]:
        """
        Updates an existing workflow document with partial fields.
        
        Args:
            workflow_id: String ID or 24-hex ObjectId string.
            workflow_update: WorkflowUpdate schema containing partial fields.
            
        Returns:
            Updated WorkflowResponse if found, otherwise None.
            
        Raises:
            DuplicateWorkflowNameError: If updated name conflicts with another workflow.
        """
        query = self._build_id_query(workflow_id)
        update_data = workflow_update.model_dump(by_alias=True, exclude_unset=True)

        if not update_data:
            return self.get_workflow_by_id(workflow_id)

        update_data["updated_at"] = now_utc()

        try:
            updated_doc = self.collection.find_one_and_update(
                query,
                {"$set": update_data},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_doc:
                return None
            return WorkflowResponse.model_validate(updated_doc)
        except DuplicateKeyError as exc:
            logger.warning("Duplicate workflow name rejected during update: %s", workflow_update.name)
            raise DuplicateWorkflowNameError(
                f"Workflow with name '{workflow_update.name}' already exists."
            ) from exc
        except PyMongoError as exc:
            logger.error("Error updating workflow '%s': %s", workflow_id, str(exc))
            raise WorkflowRepositoryError(f"Database error updating workflow: {str(exc)}") from exc

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Deletes a workflow document from MongoDB.
        
        Args:
            workflow_id: String ID or 24-hex ObjectId string.
            
        Returns:
            True if a workflow was deleted, False if no document matched.
        """
        try:
            query = self._build_id_query(workflow_id)
        except InvalidWorkflowIdError:
            return False

        try:
            result = self.collection.delete_one(query)
            return result.deleted_count > 0
        except PyMongoError as exc:
            logger.error("Error deleting workflow '%s': %s", workflow_id, str(exc))
            raise WorkflowRepositoryError(f"Database error deleting workflow: {str(exc)}") from exc
