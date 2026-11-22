from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PENDING_HUMAN = "pending_human"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BUDGET_EXCEEDED = "budget_exceeded"
    REVOKED = "revoked"
    EXPIRED = "expired"


TERMINAL_STATUSES = frozenset(
    {
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
        JobStatus.BUDGET_EXCEEDED,
        JobStatus.REVOKED,
        JobStatus.EXPIRED,
    }
)


class BudgetLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_steps: int = Field(default=8, ge=1, le=50)
    max_tool_calls: int = Field(default=8, ge=1, le=50)
    max_units: int = Field(default=4_000, ge=100, le=100_000)


class BudgetUsage(BaseModel):
    steps: int = 0
    tool_calls: int = 0
    units: int = 0


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str = Field(min_length=3, max_length=500)
    namespace: str = Field(default="default", pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    idempotency_key: str = Field(min_length=1, max_length=128)
    ttl_seconds: int = Field(default=3600, ge=30, le=604_800)
    budget: BudgetLimits = Field(default_factory=BudgetLimits)


class NamespaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    namespace: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")


@dataclass(frozen=True)
class PlanStep:
    tool: str
    arguments: dict[str, Any]
    risk: str = "low"


@dataclass
class ResearchJob:
    topic: str
    namespace: str
    idempotency_key: str
    limits: BudgetLimits
    ttl_seconds: int
    id: str = field(default_factory=lambda: uuid4().hex)
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(init=False)
    usage: BudgetUsage = field(default_factory=BudgetUsage)
    plan: list[PlanStep] = field(default_factory=list)
    cursor: int = 0
    pending_tool: str | None = None
    approved_cursor: int | None = None
    materials: list[dict[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    report: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        self.expires_at = self.created_at + timedelta(seconds=self.ttl_seconds)

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "namespace": self.namespace,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "budget": {
                "limits": self.limits.model_dump(),
                "usage": self.usage.model_dump(),
            },
            "pending_action": self.pending_tool,
            "report": self.report,
            "error": self.error,
        }
