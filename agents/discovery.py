from typing import List, Dict, Any, Optional
import asyncio
import json
from urllib.parse import urljoin

from config import Config
from utils.logging import EventLogger
from utils.validators import sanitize_url, is_safe_domain
from tools.firecrawl import FirecrawlTool
import openai


class DiscoveryPlanner:
    """Plans discovery of canonical company pages using MapWebsite + Search, ranked by LLM."""

    def __init__(self, config: Config, firecrawl: FirecrawlTool, logger: Optional[EventLogger] = None, debug: bool = False):
        self.config = config
        self.firecrawl = firecrawl
        self.logger = logger or EventLogger()
        self.debug = debug
        self.openai = openai.OpenAI(api_key=config.openai_api_key)

    async def discover_urls(self, domain: str, max_candidates: int = 15) -> List[str]:
        if not is_safe_domain(domain):
            return []
        base = sanitize_url(domain)

        # Collect candidates
        site = domain.replace("https://", "").replace("http://", "")
        mapped: List[str] = []
        s1: List[Dict[str, Any]] = []
        s2: List[Dict[str, Any]] = []

        if self.debug:
            # Debug: include a single site map to avoid dead links, plus one lightweight search
            mapped = await self.firecrawl.find_candidate_urls(domain)
            q = f"site:{site} (about OR company OR team OR leadership OR careers OR jobs) -blog -press"
            s1 = await self._web_search(q, max_results=5)
        else:
            # Full: MapWebsite + two targeted searches
            mapped = await self.firecrawl.find_candidate_urls(domain)
            q1 = f"site:{site} (about OR company OR team OR leadership) -blog -press"
            q2 = f"site:{site} (careers OR jobs) -blog -press"
            s1 = await self._web_search(q1, max_results=5)
            s2 = await self._web_search(q2, max_results=5)

        def extract_urls(items: List[Dict[str, Any]]) -> List[str]:
            urls: List[str] = []
            base_root = f"https://{site.strip('/')}"  # for resolving relative links
            for it in items:
                u = it.get("link") or it.get("url") or it.get("href")
                if isinstance(u, str):
                    # Resolve relative URLs like "/about" to absolute
                    abs_u = u
                    if u.startswith('/') and not u.startswith('//'):
                        abs_u = urljoin(base_root + '/', u)
                    urls.append(sanitize_url(abs_u))
            return urls

        candidates = mapped + extract_urls(s1) + extract_urls(s2)

        # Save last search results for reporting in WebResearcher
        self.last_search_results = []  # type: ignore[attr-defined]
        def to_brief(it: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "title": it.get("title") or it.get("name") or it.get("heading") or "",
                "link": it.get("link") or it.get("url") or it.get("href") or "",
                "snippet": it.get("snippet") or it.get("description") or it.get("content") or "",
            }
        self.last_search_results.extend([to_brief(x) for x in s1 if isinstance(x, dict)])
        self.last_search_results.extend([to_brief(x) for x in s2 if isinstance(x, dict)])
        # If search produced no results but mapping found links, surface mapped links for reporting
        if not self.last_search_results and mapped:
            for u in mapped[:6]:
                self.last_search_results.append({"title": "Mapped", "link": u, "snippet": ""})

        # If no candidates from tools in debug, fall back to deterministic paths (no extra calls)
        if not candidates:
            commons = [
                f"{base}",
                f"{base}/about",
                f"{base}/company",
                f"{base}/team",
                f"{base}/leadership",
                f"{base}/careers",
                f"{base}/jobs",
            ]
            candidates = commons

        # Dedup and cap
        seen = set()
        unique: List[str] = []
        for u in candidates:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        unique = unique[:max_candidates]

        # Ask LLM to select canonical pages
        pick = await self._llm_select(site, unique)
        # Flatten and dedup preserves order
        chosen = [p for p in [pick.get("about"), pick.get("team"), pick.get("careers")] if isinstance(p, str) and p]
        out: List[str] = []
        base_root = f"https://{site.strip('/')}"
        for u in chosen:
            if isinstance(u, str) and u.startswith('/') and not u.startswith('//'):
                u = urljoin(base_root + '/', u)
            u = sanitize_url(u)
            if u not in out:
                out.append(u)
        # Fallback to first few candidates if LLM returns nothing
        if not out:
            out = unique[:3]
        # In debug mode, limit to 2 to reduce Firecrawl calls
        return out[: (2 if self.debug else 6)]

    async def _llm_select(self, site: str, urls: List[str]) -> Dict[str, str]:
        try:
            prompt = (
                "Select the best About, Team/Leadership, and Careers URLs from this list for site "
                + site
                + ". Respond in JSON with keys about, team, careers. Prefer short paths (e.g. /about, /team, /careers). Exclude blog/press."
            )
            content = await asyncio.to_thread(
                self.openai.chat.completions.create,
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": "Return JSON only. No prose."},
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": json.dumps(urls)},
                ],
                temperature=0,
                max_tokens=200,
            )
            text = content.choices[0].message.content or "{}"
            data = json.loads(text)
            if isinstance(data, dict):
                return {
                    "about": data.get("about", ""),
                    "team": data.get("team", "") or data.get("leadership", ""),
                    "careers": data.get("careers", "") or data.get("jobs", ""),
                }
        except Exception:
            pass
        return {"about": "", "team": "", "careers": ""}

    async def _web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        # Use the same Arcade executor via FirecrawlTool (skip if unavailable e.g., tests)
        if not hasattr(self.firecrawl, "exec"):
            return []
        payload = await self.firecrawl.exec.execute(
            step="act:web_search",
            tool_name="GoogleSearch.Search",
            input={"query": query, "num_results": max_results},
        )
        results: List[Dict[str, Any]] = []
        if isinstance(payload, list):
            for it in payload:
                if isinstance(it, dict):
                    results.append(it)
        elif isinstance(payload, dict):
            for key in ("results", "data", "items", "organic_results"):
                if isinstance(payload.get(key), list):
                    results.extend([it for it in payload[key] if isinstance(it, dict)])
                    break
        return results
