"""Typed contracts shared by orchestration, persistence, and the UI."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str = Field(min_length=5, max_length=2_000)
    depth: int = Field(default=2, ge=1, le=5)
    source_types: list[str] = Field(default_factory=lambda: ["academic", "official"])


class ResearchRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    request: ResearchRequest
    status: RunStatus = RunStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: str | None = None


class AgentTask(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    agent_name: str = Field(min_length=1)
    status: RunStatus = RunStatus.QUEUED
    input_summary: str = ""
    output_summary: str = ""


class SourceDocument(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    url: HttpUrl
    title: str = ""
    source_type: str = "web"
    domain: str = ""
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    content_hash: str | None = None


class EvidenceSnippet(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    text: str = Field(min_length=1)
    locator: str = ""


class Claim(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    text: str = Field(min_length=1)
    evidence_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Citation(BaseModel):
    claim_id: UUID
    source_id: UUID
    label: str = ""


class Report(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    title: str
    summary: str
    claims: list[Claim] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class RunEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    event_type: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
