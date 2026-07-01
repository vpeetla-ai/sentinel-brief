"""LangGraph state for overnight brief runs."""

from __future__ import annotations

from typing import Any, TypedDict


class SentinelState(TypedDict, total=False):
    run_id: str
    items: list[dict[str, Any]]
    deltas: list[dict[str, Any]]
    brief_markdown: str
    eval_result: dict[str, Any]
    gateway: dict[str, Any]
    email_result: dict[str, Any]
    report_path: str
    error: str | None
    status: str
