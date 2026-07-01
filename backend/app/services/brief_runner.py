"""Run orchestration service."""

from __future__ import annotations

import uuid

from app.graph.builder import get_sentinel_graph


async def run_brief(*, run_id: str | None = None) -> dict:
    graph = get_sentinel_graph()
    initial = {"run_id": run_id or str(uuid.uuid4())}
    result = await graph.ainvoke(initial)
    return dict(result)
