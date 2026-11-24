"""
Agent domain models and schemas for AgentOps — Abyssal Intelligence.

Defines:
- AgentStatus enum
- AgentCreate (request body for creating an agent)
- AgentUpdate (request body for partial updates)
- AgentInDB (internal MongoDB document representation)
- AgentResponse (API response model, 100% compatible with frontend AgentInfo)
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.common import TimestampedModel


class AgentStatus(str, Enum):
    """
    Operational status of an autonomous subsea agent.
    Strictly aligns with AgentStatus in frontend/types/dashboard.ts.
    """
    ACTIVE = "active"
    IDLE = "idle"
    COMPUTING = "computing"
    DEGRADED = "degraded"


def compute_codenamed_depth(depth_meters: int) -> str:
    """Helper to generate standard codenamed depth description based on meters."""
    if depth_meters <= 200:
        return f"Epipelagic ({depth_meters}m)"
    elif depth_meters <= 1000:
        return f"Mesopelagic ({depth_meters}m)"
    elif depth_meters <= 4000:
        return f"Bathypelagic ({depth_meters}m)"
    elif depth_meters <= 6000:
        return f"Abyssopelagic ({depth_meters}m)"
    else:
        return f"Hadopelagic ({depth_meters}m)"


class AgentBase(BaseModel):
    """
    Base attributes shared across Agent schemas.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Display name or callsign of the agent",
        examples=["Kraken-Router v2.4"],
    )
    role: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Operational responsibility or specialization",
        examples=["Central Orchestrator & Task Decomposer"],
    )
    model: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Target LLM model powering the agent",
        examples=["Claude 3.7 Sonnet (Hybrid Reasoning)", "GPT-4o"],
    )
    status: AgentStatus = Field(
        default=AgentStatus.IDLE,
        description="Current operational lifecycle status",
    )
    codenamed_depth: Optional[str] = Field(
        default=None,
        alias="codenamedDepth",
        description="Zone codename and depth tier string",
        examples=["Hadopelagic (10,900m)"],
    )
    current_task: str = Field(
        default="Standby",
        alias="currentTask",
        max_length=500,
        description="Description of the task currently being executed",
        examples=["Decomposing high-level user objective into parallel sub-tasks"],
    )
    operational_depth_meters: int = Field(
        default=200,
        alias="operationalDepthMeters",
        ge=0,
        le=11500,
        description="Oceanographic depth rating in meters (0 to 11,500m)",
        examples=[10920],
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for LLM reasoning (0.0 to 2.0)",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=128000,
        description="Maximum token generation limit (1 to 128,000)",
    )
    system_prompt: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="System prompt and instructions configured for this agent",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    @field_validator("name", "role", "model", mode="before")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Field cannot be empty or purely whitespace")
        return v


class AgentCreate(AgentBase):
    """
    Schema for creating a new agent.
    If codenamedDepth is omitted, it is automatically derived from operationalDepthMeters.
    """
    def model_post_init(self, __context) -> None:
        if not self.codenamed_depth:
            self.codenamed_depth = compute_codenamed_depth(self.operational_depth_meters)


class AgentUpdate(BaseModel):
    """
    Schema for updating an existing agent. All fields are optional.
    """
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    role: Optional[str] = Field(default=None, min_length=2, max_length=200)
    model: Optional[str] = Field(default=None, min_length=2, max_length=100)
    status: Optional[AgentStatus] = None
    codenamed_depth: Optional[str] = Field(default=None, alias="codenamedDepth")
    current_task: Optional[str] = Field(default=None, alias="currentTask", max_length=500)
    operational_depth_meters: Optional[int] = Field(
        default=None,
        alias="operationalDepthMeters",
        ge=0,
        le=11500,
    )
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=128000)
    system_prompt: Optional[str] = Field(default=None, max_length=10000)

    # Telemetry metrics (can be updated via telemetry workers)
    memory_usage_mb: Optional[float] = Field(default=None, ge=0.0, alias="memoryUsageMb")
    tokens_processed: Optional[int] = Field(default=None, ge=0, alias="tokensProcessed")
    avg_latency_ms: Optional[float] = Field(default=None, ge=0.0, alias="avgLatencyMs")
    success_rate_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        alias="successRatePercent",
    )
    uptime_hours: Optional[float] = Field(default=None, ge=0.0, alias="uptimeHours")

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class AgentInDB(TimestampedModel, AgentBase):
    """
    Internal representation of an Agent document stored in MongoDB.
    Includes default telemetry metrics and database identifiers.
    """
    id: Optional[str] = Field(default=None, description="Database unique identifier (stringified ObjectId)")
    memory_usage_mb: float = Field(default=0.0, ge=0.0, alias="memoryUsageMb")
    tokens_processed: int = Field(default=0, ge=0, alias="tokensProcessed")
    avg_latency_ms: float = Field(default=0.0, ge=0.0, alias="avgLatencyMs")
    success_rate_percent: float = Field(default=100.0, ge=0.0, le=100.0, alias="successRatePercent")
    uptime_hours: float = Field(default=0.0, ge=0.0, alias="uptimeHours")


class AgentResponse(TimestampedModel):
    """
    API Response model returned to clients.
    Guaranteed to match the frontend AgentInfo interface in frontend/types/dashboard.ts.
    
    Frontend AgentInfo fields:
      - id: string
      - name: string
      - codenamedDepth: string
      - role: string
      - model: string
      - status: AgentStatus ("active" | "idle" | "computing" | "degraded")
      - currentTask: string
      - operationalDepthMeters: number
      - memoryUsageMb: number
      - tokensProcessed: number
      - avgLatencyMs: number
      - successRatePercent: number
      - uptimeHours: number
    """
    id: str = Field(description="Unique string identifier (e.g. 'agt-001' or stringified ObjectId)")
    name: str = Field(description="Display name of the agent")
    codenamed_depth: str = Field(alias="codenamedDepth", description="Codenamed depth zone")
    role: str = Field(description="Operational role of the agent")
    model: str = Field(description="LLM model identifier")
    status: AgentStatus = Field(description="Agent lifecycle status")
    current_task: str = Field(alias="currentTask", description="Current running task description")
    operational_depth_meters: int = Field(
        alias="operationalDepthMeters",
        description="Depth in meters",
    )
    memory_usage_mb: float = Field(
        default=0.0,
        alias="memoryUsageMb",
        description="Memory usage in megabytes",
    )
    tokens_processed: int = Field(
        default=0,
        alias="tokensProcessed",
        description="Cumulative tokens processed",
    )
    avg_latency_ms: float = Field(
        default=0.0,
        alias="avgLatencyMs",
        description="Average execution latency in milliseconds",
    )
    success_rate_percent: float = Field(
        default=100.0,
        alias="successRatePercent",
        description="Success rate percentage (0 - 100)",
    )
    uptime_hours: float = Field(
        default=0.0,
        alias="uptimeHours",
        description="Operational uptime in hours",
    )

    # Optional backend-specific configuration attributes
    temperature: float = Field(default=0.7, description="Model temperature")
    max_tokens: int = Field(default=4096, description="Model max output tokens")
    system_prompt: Optional[str] = Field(default=None, description="System instructions")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
