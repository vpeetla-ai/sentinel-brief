"""Hacker News adapters — Firebase API + Algolia AI search."""

from __future__ import annotations

import hashlib

import httpx

from app.models.items import RawItem
from app.sources.base import SourceAdapter

HN_UA = "SentinelBrief/0.1 (+https://github.com/vpeetla-ai)"


class HnFirebaseAdapter(SourceAdapter):
    async def fetch(self, *, limit: int) -> list[RawItem]:
        base = self.config["url"].rstrip("/")
        async with httpx.AsyncClient(timeout=30.0) as client:
            top = await client.get(f"{base}/topstories.json", headers={"User-Agent": HN_UA})
            top.raise_for_status()
            ids = top.json()[: limit * 2]

            items: list[RawItem] = []
            for story_id in ids:
                if len(items) >= limit:
                    break
                story_resp = await client.get(f"{base}/item/{story_id}.json", headers={"User-Agent": HN_UA})
                if story_resp.status_code != 200:
                    continue
                story = story_resp.json()
                if not story or story.get("type") != "story":
                    continue
                title = story.get("title", "")
                url = story.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
                items.append(
                    RawItem(
                        source_id=self.source_id,
                        source_label=self.source_label,
                        item_id=str(story_id),
                        title=title,
                        url=url,
                        summary=f"HN score {story.get('score', 0)} · {story.get('descendants', 0)} comments",
                        metadata={"hn_id": story_id, "score": story.get("score")},
                    )
                )
            return items


class HnAlgoliaAdapter(SourceAdapter):
    async def fetch(self, *, limit: int) -> list[RawItem]:
        api = self.config["url"]
        query = self.config.get("query", "AI")
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": limit,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(api, params=params, headers={"User-Agent": HN_UA})
            resp.raise_for_status()
            hits = resp.json().get("hits", [])

        items: list[RawItem] = []
        for hit in hits:
            object_id = hit.get("objectID", "")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            items.append(
                RawItem(
                    source_id=self.source_id,
                    source_label=self.source_label,
                    item_id=object_id or hashlib.sha256(url.encode()).hexdigest()[:16],
                    title=hit.get("title", "Untitled"),
                    url=url,
                    summary=f"HN points {hit.get('points', 0)} · AI-filtered",
                    metadata={"points": hit.get("points"), "ai_query": query},
                )
            )
        return items
