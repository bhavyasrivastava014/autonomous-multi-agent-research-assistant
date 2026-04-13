"""Pydantic schemas for request and response data."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Source(BaseModel):
    title: str = Field(..., max_length=500)
    url: HttpUrl
    snippet: str = Field(..., max_length=2000)
    rank: int
    preview: Optional[str] = None


class Stats(BaseModel):
    total_sources: int
    top_sources_used: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    synthesis_strategy: str = "extractive"
    used_cached_context: bool = False


class ResearchResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: str
    query: str
    summary: str = Field(..., max_length=6000)
    sources: List[Source] = Field(default_factory=list)
    stats: Stats
    related_research: List[dict] = Field(default_factory=list)
    error_message: Optional[str] = None


class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str
    content: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


__all__ = ["ResearchResponse", "Source", "Stats", "SearchResult"]
