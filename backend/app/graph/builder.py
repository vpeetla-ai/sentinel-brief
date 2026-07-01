"""Sentinel Brief LangGraph — governed overnight pipeline."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    archive_report,
    diff_items,
    fetch_sources,
    gateway_and_email,
    run_eval,
    write_brief,
)
from app.graph.state import SentinelState


def build_sentinel_graph():
    graph = StateGraph(SentinelState)
    graph.add_node("fetch_sources", fetch_sources)
    graph.add_node("diff_items", diff_items)
    graph.add_node("write_brief", write_brief)
    graph.add_node("run_eval", run_eval)
    graph.add_node("gateway_and_email", gateway_and_email)
    graph.add_node("archive_report", archive_report)

    graph.set_entry_point("fetch_sources")
    graph.add_edge("fetch_sources", "diff_items")
    graph.add_edge("diff_items", "write_brief")
    graph.add_edge("write_brief", "run_eval")
    graph.add_edge("run_eval", "gateway_and_email")
    graph.add_edge("gateway_and_email", "archive_report")
    graph.add_edge("archive_report", END)

    return graph.compile()


_sentinel_graph = None


def get_sentinel_graph():
    global _sentinel_graph
    if _sentinel_graph is None:
        _sentinel_graph = build_sentinel_graph()
    return _sentinel_graph
