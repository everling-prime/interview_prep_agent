from typing import Dict, List, Optional
import asyncio

from utils.logging import EventLogger
from utils.validators import is_safe_domain, sanitize_url, ensure_https
from .executor import ArcadeToolExecutor


KEY_PAGES = [
    "about", "about-us", "our-story", "company", "team", "people", "leadership",
    "careers", "jobs", "culture", "values", "mission"
]


class FirecrawlTool:
    def __init__(self, executor: ArcadeToolExecutor, logger: Optional[EventLogger] = None):
        self.exec = executor
        self.logger = logger or EventLogger()

    async def find_candidate_urls(self, domain: str) -> List[str]:
        """Return candidate URLs for about/team/etc pages, sanitized and deduped.

        Strategy:
        - Always include homepage + deterministic common paths
        - Try MapWebsite and merge any matching links
        - Cap total to ~8
        """
        if not is_safe_domain(domain):
            raise ValueError("Invalid or unsafe domain")

        base = sanitize_url(domain)
        domain_base = ensure_https(domain)

        # Start with deterministic candidates
        urls: List[str] = [
            f"{domain_base}",
            *[f"{domain_base}/{p}" for p in KEY_PAGES]
        ]

        try:
            # Try Firecrawl.MapWebsite with strict caps
            payload = await self.exec.execute(
                step="decide:map_site",
                tool_name="Firecrawl.MapWebsite",
                input={
                    "url": base,
                    "ignore_sitemap": True,
                    "include_subdomains": False,
                    "limit": 25,
                },
            )
            # Expect list of links under a key such as 'links' or 'data'
            raw_links: List[str] = []
            if isinstance(payload, dict):
                items = None
                if isinstance(payload.get("links"), list):
                    items = payload["links"]
                elif isinstance(payload.get("data"), list):
                    items = payload["data"]
                if isinstance(items, list):
                    for it in items:
                        if isinstance(it, str):
                            lu = it.lower()
                            if any(k in lu for k in KEY_PAGES):
                                urls.append(sanitize_url(it))
                        elif isinstance(it, dict) and isinstance(it.get("url"), str):
                            u = it["url"]
                            lu = u.lower()
                            if any(k in lu for k in KEY_PAGES):
                                urls.append(sanitize_url(u))
        except Exception:
            # Ignore map failures; deterministic list already populated
            pass

        # Deduplicate while preserving order
        seen = set()
        deduped: List[str] = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped[:8]

    def _extract_markdown(self, payload) -> Optional[str]:
        # Direct string payload
        if isinstance(payload, str) and payload.strip():
            return payload
        if not isinstance(payload, dict):
            return None
        # Direct field
        md = payload.get("markdown")
        if isinstance(md, str) and md.strip():
            return md
        # Nested under data
        data = payload.get("data")
        if isinstance(data, dict):
            md = data.get("markdown")
            if isinstance(md, str) and md.strip():
                return md
        # List of items
        if isinstance(data, list):
            for it in data:
                if isinstance(it, dict) and isinstance(it.get("markdown"), str) and it["markdown"].strip():
                    return it["markdown"]
        # Fallback to 'content' or 'text'
        txt = payload.get("content") or (data.get("content") if isinstance(data, dict) else None) or payload.get("text")
        if isinstance(txt, str) and txt.strip():
            return txt
        return None

    async def scrape_markdown(self, urls: List[str], max_pages: int = 8, allow_crawl_fallback: bool = True) -> Dict[str, str]:
        """Scrape given URLs to markdown via Firecrawl.ScrapeUrl with safety caps.

        If nothing is scraped, attempt a tiny CrawlWebsite fallback (depth 1, limit 5).
        """
        results: Dict[str, str] = {}
        for u in urls:
            try:
                req_url = sanitize_url(u)
                payload = await self.exec.execute(
                    step="act:scrape",
                    tool_name="Firecrawl.ScrapeUrl",
                    input={
                        "url": req_url,
                        "formats": ["markdown"],
                        "only_main_content": True,
                        "timeout": 20000,
                        "wait_for": 50,
                    },
                )
                content = self._extract_markdown(payload)
                if isinstance(content, str) and content.strip():
                    key = u.split("/")[-1] or "home"
                    results[key] = content
                    self.logger.log(step="reflect:scrape", tool="Firecrawl.ScrapeUrl", outcome="ok", duration_ms=0, extra={"url": req_url, "chars": len(content)})
                    if len(results) >= max_pages:
                        return results
                else:
                    # Retry once with relaxed settings
                    payload2 = await self.exec.execute(
                        step="act:scrape",
                        tool_name="Firecrawl.ScrapeUrl",
                        input={
                            "url": req_url,
                            "formats": ["markdown"],
                            "only_main_content": False,
                            "timeout": 25000,
                            "wait_for": 150,
                        },
                    )
                    content2 = self._extract_markdown(payload2)
                    if isinstance(content2, str) and content2.strip():
                        key = u.split("/")[-1] or "home"
                        results[key] = content2
                        self.logger.log(step="reflect:scrape", tool="Firecrawl.ScrapeUrl", outcome="ok", duration_ms=0, extra={"url": req_url, "chars": len(content2), "retry": True})
                        if len(results) >= max_pages:
                            return results
                    else:
                        self.logger.log(step="reflect:scrape", tool="Firecrawl.ScrapeUrl", outcome="empty", duration_ms=0, extra={"url": req_url})
            except Exception as e:
                self.logger.log(step="reflect:scrape", tool="Firecrawl.ScrapeUrl", outcome="error", duration_ms=0, extra={"url": u, "error": str(e)})
                continue

        if results or not allow_crawl_fallback:
            return results

        # Fallback: minimal crawl to discover a few pages
        try:
            base = urls[0] if urls else None
            if not base:
                return results
            start = await self.exec.execute(
                step="act:crawl_start",
                tool_name="Firecrawl.CrawlWebsite",
                input={
                    "url": sanitize_url(base),
                    "max_depth": 1,
                    "limit": 5,
                    "ignore_sitemap": True,
                    "allow_external_links": False,
                    "async_crawl": True,
                },
            )
            crawl_id = None
            if isinstance(start, dict):
                crawl_id = start.get("id") or start.get("job_id") or (start.get("data", {}) if isinstance(start.get("data"), dict) else {}).get("id")
            if not crawl_id:
                return results

            # Poll status briefly (faster)
            for _ in range(5):
                status = await self.exec.execute(
                    step="act:crawl_status",
                    tool_name="Firecrawl.GetCrawlStatus",
                    input={"crawl_id": crawl_id},
                )
                stat = None
                if isinstance(status, dict):
                    stat = status.get("status") or (status.get("data", {}) if isinstance(status.get("data"), dict) else {}).get("status")
                if isinstance(stat, str) and stat.lower() in {"completed", "failed", "cancelled"}:
                    break
                await asyncio.sleep(0.5)

            data = await self.exec.execute(
                step="act:crawl_data",
                tool_name="Firecrawl.GetCrawlData",
                input={"crawl_id": crawl_id},
            )
            pages = []
            if isinstance(data, dict):
                if isinstance(data.get("data"), list):
                    pages = data["data"]
                elif isinstance(data.get("pages"), list):
                    pages = data["pages"]
            # Pick pages with our keywords
            for it in pages:
                if not isinstance(it, dict):
                    continue
                url = it.get("url", "")
                if any(k in str(url).lower() for k in KEY_PAGES):
                    md = self._extract_markdown(it)
                    if isinstance(md, str) and md.strip():
                        key = str(url).split("/")[-1] or "page"
                        results[key] = md
            # If still empty, take first pages with markdown
            if not results:
                count = 0
                for it in pages:
                    if not isinstance(it, dict):
                        continue
                    md = self._extract_markdown(it)
                    url = it.get("url", "page")
                    if isinstance(md, str) and md.strip():
                        key = str(url).split("/")[-1] or f"page{count+1}"
                        results[key] = md
                        count += 1
                        if count >= 3:
                            break
            return results
        except Exception:
            return results
