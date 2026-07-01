"""Integration test for graph with mocked fetch."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.models.items import RawItem


@pytest.mark.asyncio
async def test_graph_run_with_mocked_sources(tmp_path, monkeypatch):
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    monkeypatch.setenv("REPORT_DIR", str(tmp_path / "reports"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    settings.snapshot_dir = tmp_path / "snapshots"
    settings.report_dir = tmp_path / "reports"
    settings.min_delta_items = 1

    mock_items = [
        RawItem(
            source_id="test",
            source_label="Test Source",
            item_id="a",
            title="AI agents overnight",
            url="https://example.com/a",
            summary="Agents run for days",
        ),
        RawItem(
            source_id="test",
            source_label="Test Source",
            item_id="b",
            title="Governance patterns",
            url="https://example.com/b",
            summary="Gateway before email",
        ),
        RawItem(
            source_id="test",
            source_label="Test Source",
            item_id="c",
            title="Eval gates",
            url="https://example.com/c",
            summary="Golden eval registry",
        ),
    ]

    class FakeAdapter:
        source_id = "test"

        async def fetch(self, *, limit: int):
            return mock_items[:limit]

    with patch("app.sources.base.build_adapters", return_value=[FakeAdapter()]):
        from app.services.brief_runner import run_brief

        result = await run_brief(run_id="test-run-001")
        assert result["run_id"] == "test-run-001"
        assert result.get("brief_markdown")
        assert result.get("eval_result", {}).get("passed") is True
        assert (tmp_path / "reports" / "test-run-001.json").exists()
