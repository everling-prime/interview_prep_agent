# agents/web_researcher.py
from typing import Dict, Any

from models.data_models import WebResearch, CompanyInfo
from config import Config
from tools.firecrawl import FirecrawlTool
from agents.discovery import DiscoveryPlanner
from utils.logging import EventLogger
from utils.validators import is_safe_domain


class WebResearcher:
    """Researches company online using smarter discovery + Firecrawl scraping."""

    def __init__(self, config: Config, firecrawl: FirecrawlTool, logger: EventLogger | None = None, debug: bool = False):
        self.config = config
        self.firecrawl = firecrawl
        self.discovery = DiscoveryPlanner(config, firecrawl, logger=logger, debug=debug)
        self.logger = logger or EventLogger()
        self.debug = debug

    async def research_company(self, company_domain: str) -> WebResearch:
        """Find key pages (about/team/etc) and scrape them as markdown."""
        if not is_safe_domain(company_domain):
            raise ValueError("Invalid company domain")

        company_name = self._domain_to_company_name(company_domain)

        # Perceive
        self.logger.log(step="perceive", tool="input", outcome="ok", duration_ms=0, extra={"domain": company_domain})

        # Decide -> Discover candidates using Map + Search + LLM selection
        candidates = await self.discovery.discover_urls(company_domain)
        # Limit Firecrawl activity in debug mode
        max_pages = 2 if self.debug else 6
        website_content = await self.firecrawl.scrape_markdown(candidates[:max_pages], max_pages=max_pages, allow_crawl_fallback=not self.debug)

        # Analyze results into structured info
        search_results = getattr(self.discovery, 'last_search_results', [])
        company_info = self._analyze_company_data(search_results, website_content)

        return WebResearch(
            company_domain=company_domain,
            company_name=company_name,
            search_results=search_results,
            website_content=website_content,
            structured_info=company_info,
        )

    def _analyze_company_data(self, search_results: list[dict], website_content: Dict[str, str]) -> CompanyInfo:
        recent_news: list[str] = []
        return CompanyInfo(
            mission=(website_content.get('about') or website_content.get('home') or "")[:500],
            recent_news=recent_news,
        )

    @staticmethod
    def _domain_to_company_name(domain: str) -> str:
        """Convert domain to likely company name"""
        cleaned = (domain or "").strip().lower()
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            cleaned = cleaned.split("//", 1)[-1]
        if ":" in cleaned:
            cleaned = cleaned.split(":", 1)[0]
        parts = [p for p in cleaned.split('.') if p and p != 'www']
        if not parts:
            return domain.title()

        # Drop common TLD components (handles multi-part like co.uk)
        tld_tokens = {
            "com", "org", "net", "io", "ai", "app", "dev", "gov", "edu",
            "co", "us", "uk", "ca", "au", "de", "jp", "tech", "info",
        }
        while len(parts) > 1 and parts[-1] in tld_tokens:
            parts.pop()

        base = parts[-1]
        return base.replace('-', ' ').replace('_', ' ').title()
