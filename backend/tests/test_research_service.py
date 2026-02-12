import os
import pytest

from app.services.market_research_service import MarketResearchService


@pytest.mark.asyncio
async def test_market_research_no_key(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "")
    service = MarketResearchService()
    result = await service.fetch_research_inputs(
        objective="Improve onboarding conversion",
        market_segment="B2B SaaS",
        competitors=[]
    )
    assert result["snippets"] == []
    assert result["sources"] == []
