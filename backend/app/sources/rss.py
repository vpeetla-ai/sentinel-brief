"""RSS / Atom feed adapters."""

from __future__ import annotations

import hashlib
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx

from app.models.items import RawItem
from app.sources.base import SourceAdapter


def _parse_date(entry: dict[str, Any]) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime(*parsed[:6])
            except (TypeError, ValueError):
                pass
    for key in ("published", "updated"):
        raw = entry.get(key)
        if raw:
            try:
                return parsedate_to_datetime(raw)
            except (TypeError, ValueError):
                pass
    return None


def _entry_id(entry: dict[str, Any], url: str) -> str:
    uid = entry.get("id") or entry.get("link") or url
    return hashlib.sha256(str(uid).encode()).hexdigest()[:16]


class RssAdapter(SourceAdapter):
    async def fetch(self, *, limit: int) -> list[RawItem]:
        url = self.config["url"]
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "SentinelBrief/0.1 (+https://github.com/vpeetla-ai)"})
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

        items: list[RawItem] = []
        for entry in feed.entries[:limit]:
            link = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", ""))[:500]
            items.append(
                RawItem(
                    source_id=self.source_id,
                    source_label=self.source_label,
                    item_id=_entry_id(entry, link),
                    title=entry.get("title", "Untitled").strip(),
                    url=link,
                    summary=summary,
                    published_at=_parse_date(entry),
                )
            )
        return items


class RssPartialAdapter(RssAdapter):
    """Paywalled sources — headlines only with metadata flag."""

    async def fetch(self, *, limit: int) -> list[RawItem]:
        items = await super().fetch(limit=limit)
        for item in items:
            item.metadata["paywalled"] = True
            item.metadata["access"] = "headline_only"
            if not item.summary:
                item.summary = "(Paywalled — headline only)"
        return items
