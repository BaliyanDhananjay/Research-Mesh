"""Structured JSON contracts agents must return, validated before use."""

from pydantic import BaseModel, Field


class ResearchPlan(BaseModel):
    search_queries: list[str] = Field(min_length=1, max_length=8)


class DraftClaim(BaseModel):
    text: str = Field(min_length=1)
    supporting_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class DraftReport(BaseModel):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    claims: list[DraftClaim] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
