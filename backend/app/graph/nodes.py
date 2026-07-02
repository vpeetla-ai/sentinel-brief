"""Sentinel Brief graph nodes — trace-linked observability on every step."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.graph.state import SentinelState
from app.integrations.aegis_gateway import authorize_email
from app.integrations.email import send_brief_email
from app.models.items import RawItem
from app.services.eval_gate import evaluate_brief
from app.services.snapshots import compute_deltas
from app.services.summarizer import summarize_brief
from app.sources.base import build_adapters
from app.vpeetla_observability.observe import observe_node
from app.vpeetla_observability.spans import eval_score, trace_span

logger = logging.getLogger(__name__)


@observe_node("fetch_sources")
async def fetch_sources(state: SentinelState) -> dict:
    settings = get_settings()
    run_id = state.get("run_id") or str(uuid.uuid4())
    adapters = build_adapters()
    all_items: list[RawItem] = []
    errors: list[str] = []

    logger.info("fetch_sources_started run_id=%s adapter_count=%s", run_id, len(adapters))
    for adapter in adapters:
        with trace_span(f"source.{adapter.source_id}", run_id=run_id):
            try:
                items = await adapter.fetch(limit=settings.max_items_per_source)
                all_items.extend(items)
                logger.info(
                    "source_fetched run_id=%s source_id=%s item_count=%s",
                    run_id,
                    adapter.source_id,
                    len(items),
                )
            except Exception as exc:
                errors.append(f"{adapter.source_id}: {exc}")
                logger.warning(
                    "source_fetch_failed source_id=%s error=%s",
                    adapter.source_id,
                    exc,
                )

    return {
        "run_id": run_id,
        "items": [i.model_dump(mode="json") for i in all_items],
        "error": "; ".join(errors) if errors else None,
        "status": "fetched",
    }


@observe_node("diff_items")
async def diff_items(state: SentinelState) -> dict:
    items = [RawItem.model_validate(i) for i in state.get("items", [])]
    deltas, _ = compute_deltas(items)
    logger.info("diff_completed run_id=%s delta_count=%s", state.get("run_id"), len(deltas))
    return {
        "deltas": [d.model_dump(mode="json") for d in deltas],
        "status": "diffed",
    }


@observe_node("write_brief")
async def write_brief(state: SentinelState) -> dict:
    run_id = state["run_id"]
    deltas = [RawItem.model_validate(d) for d in state.get("deltas", [])]
    markdown = summarize_brief(deltas=deltas, run_id=run_id)
    logger.info("brief_written run_id=%s markdown_chars=%s", run_id, len(markdown))
    return {"brief_markdown": markdown, "status": "summarized"}


@observe_node("run_eval")
async def run_eval(state: SentinelState) -> dict:
    deltas = [RawItem.model_validate(d) for d in state.get("deltas", [])]
    result = evaluate_brief(markdown=state.get("brief_markdown", ""), deltas=deltas)
    with eval_score("brief_gate.passed", result.passed, delta_count=len(deltas)):
        pass
    with eval_score("brief_gate.score", result.score, citation_count=result.citation_count):
        pass
    logger.info(
        "eval_completed run_id=%s passed=%s score=%s reasons=%s",
        state.get("run_id"),
        result.passed,
        result.score,
        result.reasons,
    )
    return {"eval_result": result.model_dump(), "status": "evaluated"}


@observe_node("gateway_and_email")
async def gateway_and_email(state: SentinelState) -> dict:
    eval_result = state.get("eval_result", {})
    if not eval_result.get("passed", False):
        logger.warning("email_skipped_eval_failed run_id=%s", state.get("run_id"))
        return {
            "email_result": {"status": "skipped", "reason": "eval_failed"},
            "status": "blocked_by_eval",
        }

    run_id = state["run_id"]
    settings = get_settings()
    with trace_span("gateway.authorize_email", run_id=run_id):
        authz = await authorize_email(run_id=run_id, recipient=settings.brief_recipient_email or "owner@example.com")
    gateway_payload = {
        "allowed": authz.allowed,
        "decision": authz.decision,
        "reason": authz.reason,
        "requires_approval": authz.requires_approval,
    }
    if not authz.allowed:
        logger.warning("email_blocked_gateway run_id=%s reason=%s", run_id, authz.reason)
        return {
            "gateway": gateway_payload,
            "email_result": {"status": "blocked", "reason": authz.reason},
            "status": "blocked_by_gateway",
        }

    markdown = state.get("brief_markdown", "")
    subject = f"Sentinel Brief — {datetime.now(UTC).strftime('%Y-%m-%d')}"
    with trace_span("email.send", run_id=run_id):
        email_result = await send_brief_email(
            subject=subject,
            html_body=f"<pre>{markdown}</pre>",
            text_body=markdown,
        )
    logger.info("email_sent run_id=%s status=%s", run_id, email_result.get("status"))
    return {
        "gateway": gateway_payload,
        "email_result": email_result,
        "status": "emailed",
    }


@observe_node("archive_report")
async def archive_report(state: SentinelState) -> dict:
    settings = get_settings()
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    run_id = state["run_id"]
    path = settings.report_dir / f"{run_id}.json"
    payload = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "status": state.get("status"),
        "brief_markdown": state.get("brief_markdown"),
        "eval_result": state.get("eval_result"),
        "delta_count": len(state.get("deltas", [])),
        "item_count": len(state.get("items", [])),
        "email_result": state.get("email_result"),
        "gateway": state.get("gateway"),
        "error": state.get("error"),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("report_archived run_id=%s path=%s", run_id, path)
    return {"report_path": str(path), "status": state.get("status", "archived")}
