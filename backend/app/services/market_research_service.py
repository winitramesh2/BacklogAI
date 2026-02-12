import hashlib
import os
import time
from typing import Dict, List

import httpx


class MarketResearchService:
    def __init__(self) -> None:
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search.json"
        self.cache_ttl_seconds = int(os.getenv("SERPAPI_CACHE_TTL_SECONDS", "86400"))
        self.max_searches_per_hour = int(os.getenv("SERPAPI_MAX_SEARCHES_PER_HOUR", "45"))
        self._cache: Dict[str, Dict] = {}
        self._search_timestamps: List[float] = []

    def _build_cache_key(
        self,
        objective: str,
        market_segment: str | None,
        competitors: List[str],
    ) -> str:
        payload = "|".join([
            objective.strip().lower(),
            (market_segment or "").strip().lower(),
            ",".join(sorted([c.strip().lower() for c in competitors]))
        ])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> Dict | None:
        entry = self._cache.get(key)
        if not entry:
            return None
        if time.time() - entry["timestamp"] > self.cache_ttl_seconds:
            self._cache.pop(key, None)
            return None
        return entry["value"]

    def _cache_set(self, key: str, value: Dict) -> None:
        self._cache[key] = {"timestamp": time.time(), "value": value}

    def _can_search(self) -> bool:
        cutoff = time.time() - 3600
        self._search_timestamps = [t for t in self._search_timestamps if t >= cutoff]
        return len(self._search_timestamps) < self.max_searches_per_hour

    def _build_queries(
        self,
        objective: str,
        market_segment: str | None,
        competitors: List[str],
    ) -> List[str]:
        base = objective.strip()
        segment = market_segment.strip() if market_segment else ""
        queries: List[str] = []
        queries.append(" ".join([base, segment, "market trends"]).strip())
        if competitors:
            competitor_str = " vs ".join(competitors[:2])
            queries.append(" ".join([base, competitor_str, "features"]).strip())
        else:
            queries.append(" ".join([base, segment, "competitors alternatives"]).strip())
        return [q for q in queries if q]

    async def fetch_research_inputs(
        self,
        objective: str,
        market_segment: str | None,
        competitors: List[str],
    ) -> Dict:
        if not self.api_key:
            return {"queries": [], "snippets": [], "sources": []}

        cache_key = self._build_cache_key(objective, market_segment, competitors)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        if not self._can_search():
            return {"queries": [], "snippets": [], "sources": []}

        queries = self._build_queries(objective, market_segment, competitors)
        snippets: List[str] = []
        sources: List[str] = []

        async with httpx.AsyncClient(timeout=20.0) as client:
            for query in queries:
                if not self._can_search():
                    break
                params = {
                    "api_key": self.api_key,
                    "engine": "google",
                    "q": query,
                    "num": 5,
                }
                try:
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    organic = payload.get("organic_results", [])
                    for item in organic[:5]:
                        snippet = item.get("snippet") or item.get("title") or ""
                        link = item.get("link") or ""
                        if snippet:
                            snippets.append(snippet.strip())
                        if link:
                            sources.append(link.strip())
                    self._search_timestamps.append(time.time())
                except Exception:
                    continue

        result = {
            "queries": queries,
            "snippets": snippets[:15],
            "sources": list(dict.fromkeys(sources))[:10],
        }
        self._cache_set(cache_key, result)
        return result
