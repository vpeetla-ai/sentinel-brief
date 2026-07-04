"""Tests for the SENTINEL_API_KEY gate on POST /runs.

Unauthenticated, /runs costs an LLM call and can send an email on every hit —
see the ADR for the fix. These tests confirm the gate activates only when
SENTINEL_API_KEY is set, matching the same pattern used across the org.
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_runs_open_when_no_api_key_set(monkeypatch):
    monkeypatch.delenv("SENTINEL_API_KEY", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()
    with patch("app.main.run_brief", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"run_id": "r1", "status": "done", "deltas": [], "eval_result": {}, "email_result": {}}
        resp = client.post("/runs")
    assert resp.status_code == 200
    get_settings.cache_clear()


def test_runs_rejects_missing_key_when_required(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("SENTINEL_API_KEY", "secret-key")
    get_settings.cache_clear()
    resp = client.post("/runs")
    assert resp.status_code == 401
    get_settings.cache_clear()


def test_runs_rejects_wrong_key(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("SENTINEL_API_KEY", "secret-key")
    get_settings.cache_clear()
    resp = client.post("/runs", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401
    get_settings.cache_clear()


def test_runs_accepts_correct_key(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("SENTINEL_API_KEY", "secret-key")
    get_settings.cache_clear()
    with patch("app.main.run_brief", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"run_id": "r1", "status": "done", "deltas": [], "eval_result": {}, "email_result": {}}
        resp = client.post("/runs", headers={"X-API-Key": "secret-key"})
    assert resp.status_code == 200
    get_settings.cache_clear()


def test_health_and_reports_stay_open_regardless_of_key(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("SENTINEL_API_KEY", "secret-key")
    get_settings.cache_clear()
    resp = client.get("/health")
    assert resp.status_code == 200
    get_settings.cache_clear()
