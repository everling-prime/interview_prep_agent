import asyncio
from typing import List, Dict, Any

from agents.discovery import DiscoveryPlanner


class DummyConfig:
    openai_model = "gpt-4o-mini"
    openai_api_key = "test"


class DummyFirecrawl:
    async def find_candidate_urls(self, domain: str) -> List[str]:
        return [f"https://{domain}/about"]


class DummySearch:
    def __init__(self, items: List[Dict[str, Any]]):
        self.items = items

    async def web_search(self, query: str, max_results: int = 5):
        return self.items


async def _run_discover():
    cfg = DummyConfig()
    firecrawl = DummyFirecrawl()
    # Provide relative link in search results
    search = DummySearch([{"title": "About", "link": "/team", "snippet": ""}])
    planner = DiscoveryPlanner(cfg, firecrawl, search, debug=True)

    # Bypass LLM; force selection including relative path
    async def fake_select(site: str, urls: List[str]):
        return {"about": "/about", "team": "/team", "careers": ""}

    planner._llm_select = fake_select  # type: ignore[attr-defined]
    urls = await planner.discover_urls("example.com")
    return urls


def test_discovery_resolves_relative_urls():
    urls = asyncio.run(_run_discover())
    # Expect absolute https URLs
    assert all(u.startswith("https://") for u in urls)
    assert "https://example.com/about" in urls
    assert "https://example.com/team" in urls

