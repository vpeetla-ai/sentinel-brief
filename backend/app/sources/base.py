"""Source adapter protocol and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml

from app.core.config import get_settings
from app.models.items import RawItem


class SourceAdapter(ABC):
    """Fetch normalized items from one allowlisted source."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.source_id: str = config["id"]
        self.source_label: str = config["label"]

    @abstractmethod
    async def fetch(self, *, limit: int) -> list[RawItem]:
        """Return up to `limit` items from this source."""


def load_source_configs(path: Path | None = None) -> list[dict[str, Any]]:
    settings = get_settings()
    cfg_path = path or settings.sources_config_path
    with cfg_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return [s for s in data.get("sources", []) if s.get("enabled", True)]


def build_adapters(configs: list[dict[str, Any]] | None = None) -> list[SourceAdapter]:
    from app.sources.arxiv import ArxivAdapter
    from app.sources.hn import HnAlgoliaAdapter, HnFirebaseAdapter
    from app.sources.rss import RssAdapter, RssPartialAdapter

    configs = configs or load_source_configs()
    adapters: list[SourceAdapter] = []
    kind_map: dict[str, type[SourceAdapter]] = {
        "arxiv_atom": ArxivAdapter,
        "hn_firebase": HnFirebaseAdapter,
        "hn_algolia": HnAlgoliaAdapter,
        "rss": RssAdapter,
        "rss_partial": RssPartialAdapter,
    }
    for cfg in configs:
        kind = cfg.get("kind", "rss")
        cls = kind_map.get(kind)
        if cls is None:
            continue
        adapters.append(cls(cfg))
    return adapters
