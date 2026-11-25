"""
Shared models, enums, and MongoDB utilities for AgentOps.
Provides Pydantic v2 base models, ObjectId serialization, and common timestamps.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, model_validator


class OperationalDepth(str, Enum):
    """
    Subsea operational depth layers representing agent autonomy zones.
    Matches frontend OperationalDepth in types/dashboard.ts.
    """
    EPIPELAGIC = "Epipelagic"         # 0m - 200m: Surface / API Gateway / Light Telemetry
    MESOPELAGIC = "Mesopelagic"       # 200m - 1,000m: Twilight / Routing & Orchestration
    BATHYPELAGIC = "Bathypelagic"     # 1,000m - 4,000m: Midnight / Heavy Code & Reasoning
    ABYSSOPELAGIC = "Abyssopelagic"   # 4,000m - 6,000m: Abyss / Long-term Memory & AST
    HADOPELAGIC = "Hadopelagic"       # 6,000m - 11,000m: Hadal Trenches / Deep Autonomous Goals


def now_utc() -> datetime:
    """Helper returning current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class MongoBaseModel(BaseModel):
    """
    Base Pydantic model for MongoDB documents.
    
    Features:
    - Automatically maps incoming MongoDB `_id` (ObjectId or string) to `id` (str).
    - Supports population by field name or alias.
    - Serializes datetime objects cleanly into ISO-8601 strings.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @model_validator(mode="before")
    @classmethod
    def convert_mongo_identifiers(cls, data: Any) -> Any:
        """
        Converts MongoDB `_id` into a string `id` field before validation.
        Handles:
          - Dicts with BSON ObjectId in `_id` or `id`
          - Custom string IDs (e.g., 'agt-001')
        """
        if not isinstance(data, dict):
            return data

        # Make a shallow copy to prevent mutating the original input dictionary
        data_copy = dict(data)

        # 1. If '_id' exists in the document, map it to 'id'
        if "_id" in data_copy:
            raw_id = data_copy.pop("_id")
            if "id" not in data_copy or data_copy["id"] is None:
                data_copy["id"] = str(raw_id) if raw_id is not None else None

        # 2. If 'id' is a BSON ObjectId instance, convert to string
        if "id" in data_copy and isinstance(data_copy["id"], ObjectId):
            data_copy["id"] = str(data_copy["id"])

        return data_copy


class TimestampedModel(MongoBaseModel):
    """
    Base model including created_at and updated_at UTC timestamps.
    Automatically ensures loaded datetimes are timezone-aware UTC.
    """
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    @model_validator(mode="after")
    def ensure_utc_tz(self) -> "TimestampedModel":
        if self.created_at and self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)
        if self.updated_at and self.updated_at.tzinfo is None:
            self.updated_at = self.updated_at.replace(tzinfo=timezone.utc)
        return self
