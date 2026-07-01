"""Normalized intelligence items from allowlisted sources."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawItem(BaseModel):
    """Single item from a source adapter."""

    source_id: str
    source_label: str
    item_id: str
    title: str
    url: str
    summary: str = ""
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        return f"{self.source_id}:{self.item_id}"


class BriefSection(BaseModel):
    source_id: str
    source_label: str
    items: list[RawItem]


class BriefEvalResult(BaseModel):
    passed: bool
    score: float
    reasons: list[str] = Field(default_factory=list)
    citation_count: int = 0
    delta_count: int = 0
