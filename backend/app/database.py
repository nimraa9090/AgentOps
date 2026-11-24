"""
Database module for AgentOps backend using PyMongo.
Manages MongoDB client lifecycle and provides honest connectivity health checks.
"""

import logging
from typing import Any, Dict, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError
from app.config import settings

logger = logging.getLogger("agentops.database")

# Global cached client instance (lazy-loaded)
_client: Optional[MongoClient] = None


def get_mongo_client() -> Optional[MongoClient]:
    """
    Returns the MongoDB client if MONGODB_URI is configured.
    Otherwise returns None.
    """
    global _client
    uri = settings.MONGODB_URI
    if not uri or not uri.strip():
        return None

    if _client is None:
        try:
            # 2.5 second timeout to avoid blocking server health checks
            _client = MongoClient(uri.strip(), serverSelectionTimeoutMS=2500)
        except Exception as exc:
            logger.error("Failed to initialize MongoDB client: %s", str(exc))
            _client = None

    return _client


def get_database() -> Optional[Database]:
    """
    Returns the target Database instance if MongoDB is configured and available.
    Otherwise returns None.
    """
    client = get_mongo_client()
    if client is not None:
        return client[settings.DATABASE_NAME]
    return None


def check_database_connection() -> Dict[str, Any]:
    """
    Verifies actual connectivity to MongoDB via MongoClient.admin.command('ping').

    Returns:
      - status: "not_configured" -> when MONGODB_URI is not set.
      - status: "connected"      -> when the ping command succeeds.
      - status: "error"          -> when connection fails or times out.
    """
    uri = settings.MONGODB_URI
    # 1. Honest check if MongoDB is configured
    if not uri or not uri.strip():
        logger.warning("Database health check: MONGODB_URI is not configured.")
        return {
            "status": "not_configured",
            "database": None,
            "message": "MongoDB is not configured. Set MONGODB_URI in your .env file to enable database connectivity.",
        }

    # 2. Test actual connectivity with admin ping command
    test_client: Optional[MongoClient] = None
    try:
        logger.info("Database health check: Testing MongoDB connectivity via ping command...")
        test_client = MongoClient(uri.strip(), serverSelectionTimeoutMS=2500)
        # The admin 'ping' command is standard for MongoDB health probes
        test_client.admin.command("ping")
        logger.info("Database health check: Ping succeeded. Connected to '%s'.", settings.DATABASE_NAME)
        return {
            "status": "connected",
            "database": settings.DATABASE_NAME,
            "message": "Successfully connected to MongoDB.",
        }
    except ServerSelectionTimeoutError:
        logger.error("Database health check: Connection timed out reaching MongoDB cluster.")
        return {
            "status": "error",
            "database": settings.DATABASE_NAME,
            "message": "Database connection timed out. Verify your MongoDB cluster is running, network access IP is allowed, and cluster is accessible.",
        }
    except ConnectionFailure as exc:
        logger.error("Database health check: Connection failure: %s", str(exc))
        return {
            "status": "error",
            "database": settings.DATABASE_NAME,
            "message": f"MongoDB connection failure: {str(exc)}",
        }
    except PyMongoError as exc:
        logger.error("Database health check: Driver error: %s", str(exc))
        return {
            "status": "error",
            "database": settings.DATABASE_NAME,
            "message": f"MongoDB driver error: {str(exc)}",
        }
    except Exception as exc:
        logger.error("Database health check: Unexpected error: %s", str(exc))
        return {
            "status": "error",
            "database": settings.DATABASE_NAME,
            "message": f"Unexpected error checking database: {str(exc)}",
        }
    finally:
        if test_client is not None:
            try:
                test_client.close()
            except Exception:
                pass


def close_database_connection() -> None:
    """
    Closes the global MongoDB client during application shutdown.
    """
    global _client
    if _client is not None:
        try:
            _client.close()
            logger.info("Closed MongoDB client connection pool.")
        except Exception as exc:
            logger.warning("Error while closing MongoDB client: %s", str(exc))
        _client = None
