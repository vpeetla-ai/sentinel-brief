"""FastAPI — health, runs, report archive."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.brief_runner import run_brief
from app.services.report_store import list_report_paths, resolve_report_path
from app.sources.base import load_source_configs
from app.vpeetla_observability.middleware import TraceRequestMiddleware

app = FastAPI(title="Sentinel Brief API", version="0.1.0")
settings = get_settings()
app.add_middleware(TraceRequestMiddleware, service_name=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PhaseSpan(BaseModel):
    name: str
    duration_ms: float | None = None
    status: str = "ok"
    level: str = "node"


class RunResponse(BaseModel):
    run_id: str
    status: str
    delta_count: int
    eval_passed: bool
    email_status: str | None
    phases: list[PhaseSpan] = []


def _require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    """Gate POST /runs — unauthenticated, it costs an LLM call and can send email
    on every hit. Only enforced when SENTINEL_API_KEY is set (dev/demo stays open)."""
    expected = get_settings().sentinel_api_key
    if not expected:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(401, "Invalid or missing X-API-Key")


@app.get("/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "service": "sentinel-brief",
        "cron_enabled": settings.cron_enabled,
        "mirror_reports_to_archive": settings.mirror_reports_to_archive,
        "langfuse_configured": bool(settings.langfuse_public_key and settings.langfuse_secret_key),
        "aegis_gateway_configured": bool((settings.aegisai_api_base_url or "").strip()),
    }


@app.get("/sources")
async def list_sources():
    return {"sources": load_source_configs()}


@app.get("/api/v1/ops/schedule")
async def ops_schedule():
    """Product-facing overnight schedule (env-configured). Mutations stay env/Actions."""
    settings = get_settings()
    return {
        "enabled": settings.cron_enabled,
        "hour_utc": settings.cron_hour_utc,
        "cron": f"0 {settings.cron_hour_utc} * * *",
        "timezone": "UTC",
        "mutation": "env_or_github_actions",
        "mirror_reports_to_archive": settings.mirror_reports_to_archive,
        "note": "Enable via CRON_ENABLED or GitHub Actions nightly.yml + SENTINEL_API_URL.",
    }


@app.post("/runs", response_model=RunResponse, dependencies=[Depends(_require_api_key)])
async def trigger_run():
    result = await run_brief()
    eval_result = result.get("eval_result") or {}
    email = result.get("email_result") or {}
    raw_phases = result.get("phases") or []
    phases = [
        PhaseSpan(
            name=str(p.get("name", "")),
            duration_ms=p.get("duration_ms"),
            status=str(p.get("status") or "ok"),
            level=str(p.get("level") or "node"),
        )
        for p in raw_phases
        if isinstance(p, dict) and p.get("name")
    ]
    return RunResponse(
        run_id=result.get("run_id", ""),
        status=result.get("status", "unknown"),
        delta_count=len(result.get("deltas", [])),
        eval_passed=bool(eval_result.get("passed")),
        email_status=email.get("status"),
        phases=phases,
    )


@app.get("/api/v1/ops/metrics")
async def ops_metrics(limit: int = 50):
    settings = get_settings()
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    paths = list_report_paths(settings, limit=limit)
    reports = []
    passed = 0
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        ok = bool((data.get("eval_result") or {}).get("passed"))
        if ok:
            passed += 1
        reports.append(data)
    total = len(reports)
    success = round(100.0 * passed / total, 1) if total else 100.0
    aegis_configured = bool((settings.aegisai_api_base_url or "").strip())
    langfuse_configured = bool(settings.langfuse_public_key and settings.langfuse_secret_key)
    return {
        "service": "sentinel-brief",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "total_runs": total,
        "success_rate_pct": success,
        "p95_latency_ms": None,
        "active_entities": len(load_source_configs()),
        "slo": {"target_uptime_pct": 99.5, "success_target_pct": 95.0},
        "extra": {
            "sources_monitored": len(load_source_configs()),
            "durable_archive": True,
            "mirror_reports_to_archive": settings.mirror_reports_to_archive,
            "schedule": {
                "enabled": settings.cron_enabled,
                "hour_utc": settings.cron_hour_utc,
                "mutation": "env_or_github_actions",
            },
            "llm_gateway": {
                "enabled": bool((settings.llm_gateway_url or "").strip()),
                "url_configured": bool((settings.llm_gateway_url or "").strip()),
                "tenant_id": settings.llm_gateway_tenant_id
                if (settings.llm_gateway_url or "").strip()
                else None,
                "plane": "aegis-llm-gateway",
            },
            "aegis_gateway": {
                "configured": aegis_configured,
                "enabled": bool(settings.aegisai_gateway_enabled) and aegis_configured,
                "fail_open": bool(settings.aegisai_gateway_fail_open),
            },
            "langfuse": {"configured": langfuse_configured},
        },
    }


@app.get("/api/v1/ops/observability/status")
async def observability_status():
    """Compose-plane honesty — archive SoT vs optional Langfuse / gateway notify."""
    settings = get_settings()
    aegis_configured = bool((settings.aegisai_api_base_url or "").strip())
    langfuse_configured = bool(settings.langfuse_public_key and settings.langfuse_secret_key)
    gateway_on = bool((settings.llm_gateway_url or "").strip())
    return {
        "source_of_truth": (
            "Committed archives/ + live report_dir for overnight briefs; "
            "not Langfuse (optional exporter only)"
        ),
        "exporters": [
            {
                "name": "OpsMetrics",
                "state": "live",
                "detail": "GET /api/v1/ops/metrics — run success + schedule/gateway planes",
            },
            {
                "name": "Langfuse",
                "state": "configured" if langfuse_configured else "unconfigured",
                "detail": "Optional LANGFUSE_* export of brief spans — not the report ledger",
            },
        ],
        "planes": {
            "schedule": {
                "enabled": settings.cron_enabled,
                "hour_utc": settings.cron_hour_utc,
                "mutation": "env_or_github_actions",
            },
            "mirror_reports_to_archive": settings.mirror_reports_to_archive,
            "llm_gateway": {
                "enabled": gateway_on,
                "plane": "aegis-llm-gateway",
            },
            "aegis_gateway": {
                "configured": aegis_configured,
                "enabled": bool(settings.aegisai_gateway_enabled) and aegis_configured,
                "fail_open": bool(settings.aegisai_gateway_fail_open),
                "plane": "email_notify_side_effects",
            },
            "langfuse": {"configured": langfuse_configured},
            "api_key_gated_runs": bool(settings.sentinel_api_key),
        },
        "recommendation": (
            "Treat archives + /reports as demo proof. "
            "Enable MIRROR_REPORTS_TO_ARCHIVE for durable overnight receipts; "
            "AegisAI owns email side effects when wired."
        ),
    }


@app.get("/reports")
async def list_reports(limit: int = 20):
    settings = get_settings()
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    paths = list_report_paths(settings, limit=limit)
    reports = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        reports.append(
            {
                "run_id": data.get("run_id"),
                "created_at": data.get("created_at"),
                "status": data.get("status"),
                "delta_count": data.get("delta_count"),
                "eval_passed": (data.get("eval_result") or {}).get("passed"),
                "storage": "archive" if "archives" in str(path) else "live",
            }
        )
    return {"reports": reports}


@app.get("/reports/{run_id}")
async def get_report(run_id: str):
    settings = get_settings()
    path = resolve_report_path(settings, run_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return json.loads(path.read_text(encoding="utf-8"))
