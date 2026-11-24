"""
Workflow domain models and schemas for AgentOps — Abyssal Intelligence.

Defines:
- WorkflowStatus enum (draft, active, paused, completed, failed)
- WorkflowStep (individual step within an autonomous workflow)
- WorkflowBase (shared workflow attributes)
- WorkflowCreate (request payload for creating workflows)
- WorkflowUpdate (request payload for partial updates)
- WorkflowInDB (internal MongoDB document representation)
- WorkflowResponse (API response model with stringified IDs)
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.common import TimestampedModel


class WorkflowStatus(str, Enum):
    """
    Lifecycle status of a subsea execution workflow.
    """
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStep(BaseModel):
    """
    Represents an atomic execution step within a multi-agent workflow.
    """
    step_id: str = Field(
        ...,
        alias="stepId",
        min_length=1,
        max_length=100,
        description="Unique identifier for the step within the workflow",
        examples=["step-01", "ingest-telemetry"],
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Human-readable name of the step",
        examples=["Ingest Subsea Telemetry"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional detailed description of the step action",
    )
    agent_id: Optional[str] = Field(
        default=None,
        alias="agentId",
        description="Optional reference to an assigned Agent ID",
        examples=["agt-001", "654a1b2c3d4e5f6a7b8c9d0e"],
    )
    order: int = Field(
        ...,
        ge=0,
        description="Execution sequence order (must be non-negative integer: 0, 1, 2...)",
        examples=[0],
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary for step-specific runtime configuration and parameters",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    @field_validator("step_id", "name", mode="before")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Field cannot be empty or purely whitespace")
        return v


class WorkflowBase(BaseModel):
    """
    Base attributes shared across Workflow schemas.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Display name of the workflow",
        examples=["Abyssal Trench Mapping Pipeline"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional high-level description of the workflow goals",
    )
    status: WorkflowStatus = Field(
        default=WorkflowStatus.DRAFT,
        description="Current workflow lifecycle status",
    )
    steps: List[WorkflowStep] = Field(
        default_factory=list,
        description="Ordered sequence of workflow execution steps",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_non_empty_name(cls, v: str) -> str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Workflow name cannot be empty or purely whitespace")
        return v

    @field_validator("steps")
    @classmethod
    def validate_unique_step_ids(cls, steps: List[WorkflowStep]) -> List[WorkflowStep]:
        step_ids = [s.step_id for s in steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Workflow step IDs must be unique within the workflow")
        return steps


class WorkflowCreate(WorkflowBase):
    """
    Schema for creating a new workflow.
    Defaults status to 'draft' and steps to an empty list.
    """
    pass


class WorkflowUpdate(BaseModel):
    """
    Schema for partially updating a workflow. All fields are optional.
    """
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[WorkflowStatus] = None
    steps: Optional[List[WorkflowStep]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_non_empty_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("Workflow name cannot be empty or purely whitespace")
        return v

    @field_validator("steps")
    @classmethod
    def validate_unique_step_ids(cls, steps: Optional[List[WorkflowStep]]) -> Optional[List[WorkflowStep]]:
        if steps is not None:
            step_ids = [s.step_id for s in steps]
            if len(step_ids) != len(set(step_ids)):
                raise ValueError("Workflow step IDs must be unique within the workflow")
        return steps


class WorkflowInDB(TimestampedModel, WorkflowBase):
    """
    Internal representation of a Workflow document stored in MongoDB.
    Includes database unique identifier and created/updated timestamps.
    """
    id: Optional[str] = Field(default=None, description="Database unique identifier (stringified ObjectId)")


class WorkflowResponse(TimestampedModel, WorkflowBase):
    """
    API Response model returned to clients.
    Safely serializes MongoDB ObjectId to string ID and hides raw _id.
    """
    id: str = Field(description="Unique string identifier (e.g. stringified ObjectId)")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
