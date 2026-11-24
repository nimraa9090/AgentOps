"""
Agent repository for AgentOps — Abyssal Intelligence.
Provides data access layer operations for the 'agents' collection in MongoDB.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, IndexModel, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.database import get_database
from app.models.agent import (
    AgentCreate,
    AgentResponse,
    AgentStatus,
    AgentUpdate,
)
from app.models.common import now_utc

logger = logging.getLogger("agentops.repositories.agent")


class AgentRepositoryError(Exception):
    """Base exception for agent repository errors."""
    pass


class DuplicateAgentNameError(AgentRepositoryError):
    """Raised when attempting to create or rename an agent with an existing name."""
    pass


class InvalidAgentIdError(AgentRepositoryError):
    """Raised when an invalid format is supplied for an agent identifier."""
    pass


def init_agent_indexes(db: Database) -> List[str]:
    """
    Idempotently initializes indexes on the 'agents' collection.
    
    Indexes created:
    - idx_agents_name_unique: Unique constraint on agent name (callsign).
    - idx_agents_status: Accelerated lookup by operational state (active, idle, computing, degraded).
    - idx_agents_created_at: Fast chronological sorting for timeline queries.
    
    Returns:
        List of index names created or verified by MongoDB.
    """
    collection: Collection = db["agents"]
    indexes = [
        IndexModel([("name", ASCENDING)], unique=True, name="idx_agents_name_unique"),
        IndexModel([("status", ASCENDING)], name="idx_agents_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_agents_created_at"),
    ]
    created = collection.create_indexes(indexes)
    logger.info("Ensured indexes on 'agents' collection: %s", created)
    return created


class AgentRepository:
    """
    Repository pattern managing CRUD queries and business data operations
    for the 'agents' collection in MongoDB.
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initializes repository with database instance.
        If db is not explicitly provided, uses the application global connection.
        """
        self._db = db if db is not None else get_database()
        if self._db is None:
            raise RuntimeError(
                "AgentRepository could not obtain a valid database connection. "
                "Ensure MONGODB_URI is properly configured."
            )
        self.collection: Collection = self._db["agents"]

    @staticmethod
    def _build_id_query(agent_id: str) -> Dict[str, Any]:
        """
        Constructs a safe query targeting either a BSON ObjectId or a custom string identifier.
        """
        if not agent_id or not isinstance(agent_id, str) or not agent_id.strip():
            raise InvalidAgentIdError("Agent ID must be a non-empty string.")

        clean_id = agent_id.strip()
        if ObjectId.is_valid(clean_id):
            return {"$or": [{"_id": ObjectId(clean_id)}, {"_id": clean_id}, {"id": clean_id}]}
        return {"$or": [{"_id": clean_id}, {"id": clean_id}]}

    def create_agent(self, agent_data: AgentCreate) -> AgentResponse:
        """
        Inserts a new agent document into MongoDB.
        
        Args:
            agent_data: Validated AgentCreate model.
            
        Returns:
            AgentResponse matching frontend AgentInfo.
            
        Raises:
            DuplicateAgentNameError: If an agent with the same name already exists.
            AgentRepositoryError: For general database insertion failures.
        """
        # Serialize fields using aliases (camelCase matching frontend)
        doc = agent_data.model_dump(by_alias=True)

        # Set default telemetry counters and metadata
        timestamp = now_utc()
        doc["memoryUsageMb"] = 0.0
        doc["tokensProcessed"] = 0
        doc["avgLatencyMs"] = 0.0
        doc["successRatePercent"] = 100.0
        doc["uptimeHours"] = 0.0
        doc["created_at"] = timestamp
        doc["updated_at"] = timestamp

        try:
            result = self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            return AgentResponse.model_validate(doc)
        except DuplicateKeyError as exc:
            logger.warning("Duplicate agent name rejected: %s", agent_data.name)
            raise DuplicateAgentNameError(
                f"Agent with name '{agent_data.name}' already exists."
            ) from exc
        except PyMongoError as exc:
            logger.error("Failed to insert agent '%s': %s", agent_data.name, str(exc))
            raise AgentRepositoryError(f"Database error creating agent: {str(exc)}") from exc

    def get_agent_by_id(self, agent_id: str) -> Optional[AgentResponse]:
        """
        Finds a single agent by its ObjectId or string ID.
        
        Args:
            agent_id: String ID or 24-hex ObjectId string.
            
        Returns:
            AgentResponse if found, otherwise None.
        """
        try:
            query = self._build_id_query(agent_id)
        except InvalidAgentIdError:
            return None

        try:
            doc = self.collection.find_one(query)
            if not doc:
                return None
            return AgentResponse.model_validate(doc)
        except PyMongoError as exc:
            logger.error("Error retrieving agent '%s': %s", agent_id, str(exc))
            raise AgentRepositoryError(f"Database error retrieving agent: {str(exc)}") from exc

    def get_all_agents(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[AgentStatus] = None,
    ) -> Tuple[List[AgentResponse], int]:
        """
        Retrieves paginated list of agents and the total count matching filters.
        
        Args:
            skip: Number of documents to skip (offset, >= 0).
            limit: Maximum documents to return (page size, 1 to 100).
            status: Optional AgentStatus filter.
            
        Returns:
            Tuple of (list of AgentResponse items, total_count).
        """
        query: Dict[str, Any] = {}
        if status is not None:
            query["status"] = status.value if hasattr(status, "value") else str(status)

        # Enforce safe pagination bounds
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
            agents = [AgentResponse.model_validate(doc) for doc in cursor]
            return agents, total_count
        except PyMongoError as exc:
            logger.error("Error querying agents list: %s", str(exc))
            raise AgentRepositoryError(f"Database error fetching agents: {str(exc)}") from exc

    def update_agent(
        self,
        agent_id: str,
        agent_update: AgentUpdate,
    ) -> Optional[AgentResponse]:
        """
        Updates an existing agent document with partial fields.
        
        Args:
            agent_id: String ID or 24-hex ObjectId string.
            agent_update: AgentUpdate schema containing partial fields.
            
        Returns:
            Updated AgentResponse if found, otherwise None.
            
        Raises:
            DuplicateAgentNameError: If updated name conflicts with another agent.
        """
        query = self._build_id_query(agent_id)
        update_data = agent_update.model_dump(by_alias=True, exclude_unset=True)

        if not update_data:
            # Nothing to update; return existing record
            return self.get_agent_by_id(agent_id)

        update_data["updated_at"] = now_utc()

        try:
            updated_doc = self.collection.find_one_and_update(
                query,
                {"$set": update_data},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_doc:
                return None
            return AgentResponse.model_validate(updated_doc)
        except DuplicateKeyError as exc:
            logger.warning("Duplicate agent name rejected during update: %s", agent_update.name)
            raise DuplicateAgentNameError(
                f"Agent with name '{agent_update.name}' already exists."
            ) from exc
        except PyMongoError as exc:
            logger.error("Error updating agent '%s': %s", agent_id, str(exc))
            raise AgentRepositoryError(f"Database error updating agent: {str(exc)}") from exc

    def delete_agent(self, agent_id: str) -> bool:
        """
        Deletes an agent document from MongoDB.
        
        Args:
            agent_id: String ID or 24-hex ObjectId string.
            
        Returns:
            True if an agent was deleted, False if no document matched.
        """
        try:
            query = self._build_id_query(agent_id)
        except InvalidAgentIdError:
            return False

        try:
            result = self.collection.delete_one(query)
            return result.deleted_count > 0
        except PyMongoError as exc:
            logger.error("Error deleting agent '%s': %s", agent_id, str(exc))
            raise AgentRepositoryError(f"Database error deleting agent: {str(exc)}") from exc
