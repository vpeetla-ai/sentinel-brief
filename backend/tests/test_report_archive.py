"""Tests for durable archive fallback (P3.1)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_reports_include_committed_archive():
    resp = client.get("/reports")
    assert resp.status_code == 200
    reports = resp.json()["reports"]
    assert any(r.get("run_id") == "archive-sample-2026-07-02" for r in reports)


def test_get_archived_sample():
    resp = client.get("/reports/archive-sample-2026-07-02")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == "archive-sample-2026-07-02"
    assert body.get("archive_source") == "committed_durable"
