"""Tests for snapshot deltas."""

from app.models.items import RawItem
from app.services.snapshots import compute_deltas, load_snapshot


def test_compute_deltas_detects_new_items(tmp_path, monkeypatch):
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    settings.snapshot_dir = tmp_path

    items = [
        RawItem(
            source_id="hn",
            source_label="HN",
            item_id="1",
            title="First",
            url="https://hn/1",
        )
    ]
    deltas, _ = compute_deltas(items)
    assert len(deltas) == 1
    assert "hn:1" in load_snapshot("hn")

    deltas2, _ = compute_deltas(items)
    assert len(deltas2) == 0
