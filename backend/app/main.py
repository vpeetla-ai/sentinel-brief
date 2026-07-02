"""FastAPI — health, runs, report archive."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.brief_runner import run_brief
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


class RunResponse(BaseModel):
    run_id: str
    status: str
    delta_count: int
    eval_passed: bool
    email_status: str | None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sentinel-brief"}


@app.get("/sources")
async def list_sources():
    return {"sources": load_source_configs()}


@app.post("/runs", response_model=RunResponse)
async def trigger_run():
    result = await run_brief()
    eval_result = result.get("eval_result") or {}
    email = result.get("email_result") or {}
    return RunResponse(
        run_id=result.get("run_id", ""),
        status=result.get("status", "unknown"),
        delta_count=len(result.get("deltas", [])),
        eval_passed=bool(eval_result.get("passed")),
        email_status=email.get("status"),
    )


@app.get("/reports")
async def list_reports(limit: int = 20):
    settings = get_settings()
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(settings.report_dir.glob("*.json"), reverse=True)[:limit]
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
            }
        )
    return {"reports": reports}


@app.get("/reports/{run_id}")
async def get_report(run_id: str):
    settings = get_settings()
    path: Path = settings.report_dir / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return json.loads(path.read_text(encoding="utf-8"))
