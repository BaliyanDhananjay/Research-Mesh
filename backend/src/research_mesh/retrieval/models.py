"""Contracts for search providers before content is fetched and cited."""

from pydantic import BaseModel, Field, HttpUrl


class SourceCandidate(BaseModel):
    url: HttpUrl
    title: str = ""
    snippet: str = ""
    source_type: str = "web"
    domain: str = ""
    published_year: int | None = Field(default=None, ge=1900, le=2100)
    is_primary_source: bool = False
