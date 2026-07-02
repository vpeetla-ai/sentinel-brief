"""Run orchestration — trace-linked LangGraph execution."""

from __future__ import annotations

import uuid

from app.vpeetla_observability.context import bind_trace_context, clear_trace_context
from app.vpeetla_observability.export import export_trace_summary
from app.vpeetla_observability.recorder import TraceRecorder, set_recorder
from app.vpeetla_observability.spans import system_span

from app.graph.builder import get_sentinel_graph


async def run_brief(*, run_id: str | None = None) -> dict:
    rid = run_id or str(uuid.uuid4())
    recorder = TraceRecorder.create(run_id=rid, trace_id=rid, service="sentinel-brief")
    set_recorder(recorder)
    bind_trace_context(run_id=rid, trace_id=rid, root_trace_id=rid)
    recorder.ensure_langfuse_root("sentinel_brief.run")

    graph = get_sentinel_graph()
    initial = {"run_id": rid, "trace_id": rid}

    try:
        with system_span("sentinel_brief.run", run_id=rid):
            result = await graph.ainvoke(initial)
        out = dict(result)
        eval_result = out.get("eval_result") or {}
        recorder.record_eval("brief.passed", bool(eval_result.get("passed")))
        export_trace_summary(recorder, trace_name="sentinel_brief.run")
        return out
    finally:
        set_recorder(None)
        clear_trace_context()
