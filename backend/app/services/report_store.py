"""Report path resolution — live disk + committed durable archives (P3.1)."""

from __future__ import annotations

from pathlib import Path

from app.core.config import ROOT, Settings


def archive_dir(settings: Settings | None = None) -> Path:
    if settings and getattr(settings, "archive_dir", None):
        return Path(settings.archive_dir)
    return ROOT / "archives"


def report_search_dirs(settings: Settings) -> list[Path]:
    """Prefer live report_dir; fall back to committed archives/."""
    dirs = [Path(settings.report_dir), archive_dir(settings)]
    # de-dupe while preserving order
    seen: set[str] = set()
    out: list[Path] = []
    for d in dirs:
        key = str(d.resolve()) if d.exists() else str(d)
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def list_report_paths(settings: Settings, limit: int = 20) -> list[Path]:
    paths: list[Path] = []
    for d in report_search_dirs(settings):
        if not d.exists():
            continue
        paths.extend(d.glob("*.json"))
    paths = sorted(paths, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    return paths[:limit]


def resolve_report_path(settings: Settings, run_id: str) -> Path | None:
    for d in report_search_dirs(settings):
        path = d / f"{run_id}.json"
        if path.exists():
            return path
    return None
