"""
Execution repository for AgentOps — Abyssal Intelligence.
Provides data access layer operations for the 'executions' collection in MongoDB.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, IndexModel, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.database import get_database
from app.models.common import now_utc
from app.models.execution import (
    ExecutionCreate,
    ExecutionInDB,
    ExecutionResponse,
    ExecutionStatus,
    ExecutionUpdate,
)

logger = logging.getLogger("agentops.repositories.execution")


class ExecutionRepositoryError(Exception):
    """Base exception for execution repository errors."""
    pass


class InvalidExecutionIdError(ExecutionRepositoryError):
    """Raised when an invalid format is supplied for an execution identifier."""
    pass


def init_execution_indexes(db: Database) -> List[str]:
    """
    Idempotently initializes indexes on the 'executions' collection.
    
    Indexes created:
    - idx_executions_workflow_id: Fast lookup by associated workflowId.
    - idx_executions_status: Fast filtering by execution status (pending, running, etc.).
    - idx_executions_created_at: Fast chronological sorting for execution timelines.
    - idx_executions_workflow_created_at: Compound index covering recency-sorted workflow queries.
    
    Returns:
        List of index names created or verified by MongoDB.
    """
    collection: Collection = db["executions"]
    indexes = [
        IndexModel([("workflowId", ASCENDING)], name="idx_executions_workflow_id"),
        IndexModel([("status", ASCENDING)], name="idx_executions_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_executions_created_at"),
        IndexModel(
            [("workflowId", ASCENDING), ("created_at", DESCENDING)],
            name="idx_executions_workflow_created_at",
        ),
    ]
    created = collection.create_indexes(indexes)
    logger.info("Ensured indexes on 'executions' collection: %s", created)
    return created


class ExecutionRepository:
    """
    Repository pattern managing CRUD queries and business data operations
    for the 'executions' collection in MongoDB.
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initializes repository with database instance.
        If db is not explicitly provided, uses the application global connection.
        """
        self._db = db if db is not None else get_database()
        if self._db is None:
            raise RuntimeError(
                "ExecutionRepository could not obtain a valid database connection. "
                "Ensure MONGODB_URI is properly configured."
            )
        self.collection: Collection = self._db["executions"]

    @staticmethod
    def _build_id_query(execution_id: str) -> Dict[str, Any]:
        """
        Constructs a safe query targeting either a BSON ObjectId or a custom string identifier.
        """
        if not execution_id or not isinstance(execution_id, str) or not execution_id.strip():
            raise InvalidExecutionIdError("Execution ID must be a non-empty string.")

        clean_id = execution_id.strip()
        if ObjectId.is_valid(clean_id):
            return {"$or": [{"_id": ObjectId(clean_id)}, {"_id": clean_id}, {"id": clean_id}]}
        return {"$or": [{"_id": clean_id}, {"id": clean_id}]}

    def create_execution(self, execution_data: ExecutionCreate) -> ExecutionResponse:
        """
        Inserts a new execution document into MongoDB initialized in PENDING state.
        
        Args:
            execution_data: Validated ExecutionCreate payload.
            
        Returns:
            ExecutionResponse matching client contract.
            
        Raises:
            ExecutionRepositoryError: For general database insertion failures.
        """
        # Construct internal representation ensuring defaults
        in_db = ExecutionInDB(
            workflow_id=execution_data.workflow_id,
            parameters=execution_data.parameters,
            status=ExecutionStatus.PENDING,
            steps=[],
        )
        doc = in_db.model_dump(by_alias=True)
        # Remove placeholder None id so MongoDB generates _id
        doc.pop("id", None)

        timestamp = now_utc()
        doc["created_at"] = timestamp
        doc["updated_at"] = timestamp

        try:
            result = self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            return ExecutionResponse.model_validate(doc)
        except PyMongoError as exc:
            logger.error("Failed to insert execution for workflow '%s': %s", execution_data.workflow_id, str(exc))
            raise ExecutionRepositoryError(f"Database error creating execution: {str(exc)}") from exc

    def get_execution_by_id(self, execution_id: str) -> Optional[ExecutionResponse]:
        """
        Finds a single execution by its ObjectId or string ID.
        
        Args:
            execution_id: String ID or 24-hex ObjectId string.
            
        Returns:
            ExecutionResponse if found, otherwise None.
        """
        try:
            query = self._build_id_query(execution_id)
        except InvalidExecutionIdError:
            return None

        try:
            doc = self.collection.find_one(query)
            if not doc:
                return None
            return ExecutionResponse.model_validate(doc)
        except PyMongoError as exc:
            logger.error("Error retrieving execution '%s': %s", execution_id, str(exc))
            raise ExecutionRepositoryError(f"Database error retrieving execution: {str(exc)}") from exc

    def get_all_executions(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[ExecutionStatus] = None,
        workflow_id: Optional[str] = None,
    ) -> Tuple[List[ExecutionResponse], int]:
        """
        Retrieves paginated list of executions and total count matching filters.
        
        Args:
            skip: Number of documents to skip (offset, >= 0).
            limit: Maximum documents to return (page size, 1 to 100).
            status: Optional ExecutionStatus filter.
            workflow_id: Optional workflowId filter.
            
        Returns:
            Tuple of (list of ExecutionResponse items, total_count).
        """
        query: Dict[str, Any] = {}
        if status is not None:
            query["status"] = status.value if hasattr(status, "value") else str(status)
        if workflow_id is not None:
            query["workflowId"] = workflow_id

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
            executions = [ExecutionResponse.model_validate(doc) for doc in cursor]
            return executions, total_count
        except PyMongoError as exc:
            logger.error("Error querying executions list: %s", str(exc))
            raise ExecutionRepositoryError(f"Database error fetching executions: {str(exc)}") from exc

    def update_execution(
        self,
        execution_id: str,
        execution_update: ExecutionUpdate,
    ) -> Optional[ExecutionResponse]:
        """
        Updates an existing execution document with partial fields.
        
        Args:
            execution_id: String ID or 24-hex ObjectId string.
            execution_update: ExecutionUpdate schema containing partial fields.
            
        Returns:
            Updated ExecutionResponse if found, otherwise None.
        """
        query = self._build_id_query(execution_id)
        update_data = execution_update.model_dump(by_alias=True, exclude_unset=True)

        if not update_data:
            return self.get_execution_by_id(execution_id)

        update_data["updated_at"] = now_utc()

        try:
            updated_doc = self.collection.find_one_and_update(
                query,
                {"$set": update_data},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_doc:
                return None
            return ExecutionResponse.model_validate(updated_doc)
        except PyMongoError as exc:
            logger.error("Error updating execution '%s': %s", execution_id, str(exc))
            raise ExecutionRepositoryError(f"Database error updating execution: {str(exc)}") from exc

    def delete_execution(self, execution_id: str) -> bool:
        """
        Deletes an execution document from MongoDB.
        
        Args:
            execution_id: String ID or 24-hex ObjectId string.
            
        Returns:
            True if an execution was deleted, False if no document matched.
        """
        try:
            query = self._build_id_query(execution_id)
        except InvalidExecutionIdError:
            return False

        try:
            result = self.collection.delete_one(query)
            return result.deleted_count > 0
        except PyMongoError as exc:
            logger.error("Error deleting execution '%s': %s", execution_id, str(exc))
            raise ExecutionRepositoryError(f"Database error deleting execution: {str(exc)}") from exc
