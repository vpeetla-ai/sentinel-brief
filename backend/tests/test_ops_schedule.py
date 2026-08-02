"""Schedule + ops honesty for Sentinel overnight brief."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_ops_schedule_returns_overnight_shape(monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("CRON_ENABLED", "true")
    monkeypatch.setenv("CRON_HOUR_UTC", "7")
    get_settings.cache_clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ops/schedule")

    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["hour_utc"] == 7
    assert data["timezone"] == "UTC"
    assert data["mutation"] == "env_or_github_actions"
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ops_metrics_includes_schedule_and_observability(monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("MIRROR_REPORTS_TO_ARCHIVE", "true")
    monkeypatch.setenv("AEGISAI_API_BASE_URL", "https://aegis.example")
    get_settings.cache_clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ops/metrics")

    assert response.status_code == 200
    extra = response.json()["extra"]
    assert extra["mirror_reports_to_archive"] is True
    assert "schedule" in extra
    assert extra["aegis_gateway"]["configured"] is True
    assert "langfuse" in extra
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_observability_status_compose_planes(monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("MIRROR_REPORTS_TO_ARCHIVE", "true")
    monkeypatch.setenv("AEGISAI_API_BASE_URL", "https://aegis.example")
    monkeypatch.setenv("LLM_GATEWAY_URL", "https://llm.example")
    get_settings.cache_clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ops/observability/status")

    assert response.status_code == 200
    data = response.json()
    assert "source_of_truth" in data
    assert "recommendation" in data
    planes = data["planes"]
    assert planes["mirror_reports_to_archive"] is True
    assert planes["llm_gateway"]["plane"] == "aegis-llm-gateway"
    assert planes["aegis_gateway"]["configured"] is True
    names = {e["name"] for e in data["exporters"]}
    assert "OpsMetrics" in names
    assert "Langfuse" in names
    get_settings.cache_clear()
