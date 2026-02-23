import asyncio
import os

from app.services.market_research_service import MarketResearchService


def test_market_research_no_key(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "")
    service = MarketResearchService()
    result = asyncio.run(
        service.fetch_research_inputs(
            objective="Improve onboarding conversion",
            market_segment="B2B SaaS",
            competitors=[]
        )
    )
    assert result["snippets"] == []
    assert result["sources"] == []
    assert result["quality"]["source_count"] == 0


def test_research_query_strategy_expands_query_types():
    service = MarketResearchService()
    queries = service._build_queries(
        objective="Improve onboarding completion",
        market_segment="B2B SaaS",
        competitors=["Linear", "Productboard"],
    )
    assert len(queries) >= 4
