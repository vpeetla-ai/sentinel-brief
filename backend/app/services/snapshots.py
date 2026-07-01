"""Snapshot store and delta detection."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.models.items import RawItem


def _snapshot_path(source_id: str) -> Path:
    settings = get_settings()
    settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
    return settings.snapshot_dir / f"{source_id}.json"


def load_snapshot(source_id: str) -> set[str]:
    path = _snapshot_path(source_id)
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("fingerprints", []))


def save_snapshot(source_id: str, fingerprints: set[str]) -> None:
    path = _snapshot_path(source_id)
    payload = {
        "source_id": source_id,
        "updated_at": datetime.now(UTC).isoformat(),
        "fingerprints": sorted(fingerprints),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def compute_deltas(items: list[RawItem]) -> tuple[list[RawItem], list[RawItem]]:
    """Return (delta_items, all_seen_items) updating snapshots per source."""
    by_source: dict[str, list[RawItem]] = {}
    for item in items:
        by_source.setdefault(item.source_id, []).append(item)

    deltas: list[RawItem] = []
    for source_id, source_items in by_source.items():
        seen = load_snapshot(source_id)
        new_fps = {i.fingerprint for i in source_items}
        for item in source_items:
            if item.fingerprint not in seen:
                deltas.append(item)
        save_snapshot(source_id, seen | new_fps)
    return deltas, items
