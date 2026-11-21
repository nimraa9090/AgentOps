"""
Database module for AgentOps backend using PyMongo.
Manages MongoDB client lifecycle and provides honest connectivity health checks.
"""

from typing import Any, Dict, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError
from app.config import settings

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
        except Exception:
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
    Verifies actual connectivity to MongoDB.

    Returns:
      - status: "not_configured" -> when MONGODB_URI is not set.
      - status: "connected"      -> when the ping command succeeds.
      - status: "error"          -> when connection fails or times out.
    """
    uri = settings.MONGODB_URI
    # 1. Honest check if MongoDB is configured
    if not uri or not uri.strip():
        return {
            "status": "not_configured",
            "database": None,
            "message": "MongoDB is not configured. Set MONGODB_URI in your .env file to enable database connectivity.",
        }

    # 2. Test actual connectivity with ping command
    test_client: Optional[MongoClient] = None
    try:
        test_client = MongoClient(uri.strip(), serverSelectionTimeoutMS=2500)
        # The admin 'ping' command is standard for MongoDB health probes
        test_client.admin.command("ping")
        return {
            "status": "connected",
            "database": settings.DATABASE_NAME,
            "message": "Successfully connected to MongoDB.",
        }
    except ServerSelectionTimeoutError:
        return {
            "status": "error",
            "database": settings.DATABASE_NAME,
            "message": "Database connection timed out. Verify your MongoDB server is running and accessible.",
        }
    except ConnectionFailure as exc:
        return {
            "status": "error",
            "database": settings.DATABASE_NAME,
            "message": f"MongoDB connection failure: {str(exc)}",
        }
    except PyMongoError as exc:
        return {
            "status": "error",
            "database": settings.DATABASE_NAME,
            "message": f"MongoDB driver error: {str(exc)}",
        }
    except Exception as exc:
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
        except Exception:
            pass
        _client = None
