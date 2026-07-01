"""arXiv cs.AI Atom API adapter."""

from __future__ import annotations

from datetime import datetime
from xml.etree import ElementTree

import httpx

from app.models.items import RawItem
from app.sources.base import SourceAdapter

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivAdapter(SourceAdapter):
    async def fetch(self, *, limit: int) -> list[RawItem]:
        base = self.config["url"]
        category = self.config.get("category", "cs.AI")
        params = {
            "search_query": f"cat:{category}",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": limit,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(base, params=params)
            resp.raise_for_status()
            root = ElementTree.fromstring(resp.text)

        items: list[RawItem] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            arxiv_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
            title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "")[:500]
            link_el = entry.find("atom:link[@rel='alternate']", ATOM_NS)
            url = link_el.get("href") if link_el is not None else arxiv_id
            published_raw = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
            published_at = None
            if published_raw:
                try:
                    published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                except ValueError:
                    pass
            short_id = arxiv_id.rsplit("/", maxsplit=1)[-1]
            items.append(
                RawItem(
                    source_id=self.source_id,
                    source_label=self.source_label,
                    item_id=short_id,
                    title=title.replace("\n", " "),
                    url=url,
                    summary=summary.replace("\n", " "),
                    published_at=published_at,
                    metadata={"arxiv_id": short_id},
                )
            )
        return items
