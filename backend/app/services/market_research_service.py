import hashlib
import os
import re
import time
from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import urlparse

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
        queries.append(" ".join([base, segment, "user pain points complaints"]).strip())
        if competitors:
            competitor_str = " vs ".join(competitors[:2])
            queries.append(" ".join([base, competitor_str, "features"]).strip())
            queries.append(" ".join([base, competitor_str, "pricing packaging comparison"]).strip())
        else:
            queries.append(" ".join([base, segment, "competitors alternatives"]).strip())
            queries.append(" ".join([base, segment, "best practices implementation benchmark"]).strip())
        return [q for q in queries if q]

    @staticmethod
    def _extract_domain(link: str) -> str:
        try:
            hostname = urlparse(link).hostname or ""
        except Exception:
            return ""
        if hostname.startswith("www."):
            return hostname[4:]
        return hostname

    @staticmethod
    def _parse_freshness_days(value: str | None) -> int | None:
        if not value:
            return None
        raw = value.strip().lower()
        if "day" in raw:
            digits = re.findall(r"\d+", raw)
            return int(digits[0]) if digits else 1
        if "week" in raw:
            digits = re.findall(r"\d+", raw)
            return (int(digits[0]) if digits else 1) * 7
        if "month" in raw:
            digits = re.findall(r"\d+", raw)
            return (int(digits[0]) if digits else 1) * 30
        if "year" in raw:
            digits = re.findall(r"\d+", raw)
            return (int(digits[0]) if digits else 1) * 365

        for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
                delta = datetime.now(timezone.utc) - parsed
                return max(0, delta.days)
            except ValueError:
                continue
        return None

    async def fetch_research_inputs(
        self,
        objective: str,
        market_segment: str | None,
        competitors: List[str],
    ) -> Dict:
        if not self.api_key:
            return {
                "queries": [],
                "snippets": [],
                "sources": [],
                "source_details": [],
                "quality": {
                    "source_count": 0,
                    "unique_domain_count": 0,
                    "citation_coverage": 0.0,
                    "freshness_coverage": 0.0,
                },
            }

        cache_key = self._build_cache_key(objective, market_segment, competitors)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        if not self._can_search():
            return {
                "queries": [],
                "snippets": [],
                "sources": [],
                "source_details": [],
                "quality": {
                    "source_count": 0,
                    "unique_domain_count": 0,
                    "citation_coverage": 0.0,
                    "freshness_coverage": 0.0,
                },
            }

        queries = self._build_queries(objective, market_segment, competitors)
        snippets: List[str] = []
        source_details: List[Dict] = []
        seen_urls: set[str] = set()

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
                        domain = self._extract_domain(link)
                        if not link or not domain:
                            continue
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)

                        if snippet:
                            snippets.append(snippet.strip())
                        source_details.append(
                            {
                                "id": len(source_details) + 1,
                                "url": link.strip(),
                                "domain": domain,
                                "title": (item.get("title") or "").strip() or None,
                                "snippet": snippet.strip() if snippet else None,
                                "freshness_days": self._parse_freshness_days(item.get("date")),
                            }
                        )
                    self._search_timestamps.append(time.time())
                except Exception:
                    continue

        sources = [detail["url"] for detail in source_details]
        unique_domains = {detail["domain"] for detail in source_details}
        freshness_known = [d for d in source_details if d.get("freshness_days") is not None]

        result = {
            "queries": queries,
            "snippets": snippets[:15],
            "sources": list(dict.fromkeys(sources))[:12],
            "source_details": source_details[:12],
            "quality": {
                "source_count": min(len(source_details), 12),
                "unique_domain_count": len(unique_domains),
                "citation_coverage": 0.0,
                "freshness_coverage": round(len(freshness_known) / len(source_details), 2) if source_details else 0.0,
            },
        }
        self._cache_set(cache_key, result)
        return result
