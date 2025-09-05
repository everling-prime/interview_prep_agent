# agents/native_search.py
import requests
import asyncio
from typing import List, Dict, Any
import json
from urllib.parse import quote_plus

class NativeSearcher:
    """Native search implementation using free APIs"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.session = requests.Session()
        
    async def search_company_info(self, company_name: str) -> List[Dict[str, Any]]:
        """Search for company information using multiple free sources"""
        search_queries = [
            f"{company_name} recent news 2024",
            f"{company_name} about company mission",
            f"{company_name} careers culture",
            f"{company_name} product launch",
            f"{company_name} funding growth"
        ]
        
        all_results = []
        
        for query in search_queries:
            try:
                if self.debug:
                    print(f"  🔎 Searching: {query}")
                
                # Try DuckDuckGo first (most reliable)
                results = await self._search_duckduckgo(query)
                
                # If DuckDuckGo fails, try SerpAPI free tier
                if not results:
                    results = await self._search_serpapi_free(query)
                
                all_results.extend(results)
                
                if self.debug:
                    print(f"    ✓ Found {len(results)} results for: {query}")
                
                # Be respectful with rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                if self.debug:
                    print(f"    ⚠️  Error searching for '{query}': {str(e)}")
                continue
        
        print(f"📊 Found {len(all_results)} total search results")
        return all_results
    
    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo Instant Answer API (Free)"""
        try:
            # DuckDuckGo Instant Answer API
            encoded_query = quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            response = await asyncio.to_thread(
                self.session.get, url, timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract results from DuckDuckGo response
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:5]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            'query': query,
                            'title': topic.get('Text', '')[:100],
                            'snippet': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'date': '',
                            'source': 'duckduckgo'
                        })
            
            # Also check abstract
            if data.get('Abstract'):
                results.append({
                    'query': query,
                    'title': data.get('Heading', query),
                    'snippet': data.get('Abstract'),
                    'url': data.get('AbstractURL', ''),
                    'date': '',
                    'source': 'duckduckgo'
                })
            
            return results
            
        except Exception as e:
            if self.debug:
                print(f"    ⚠️  DuckDuckGo search failed: {e}")
    async def _search_news_feeds(self, query: str, company_name: str) -> List[Dict[str, Any]]:
        """Search news feeds and RSS for company mentions"""
        try:
            results = []
            
            # Try searching Google News RSS (no API key needed)
            encoded_query = quote_plus(query)
            news_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            response = await asyncio.to_thread(
                self.session.get, news_url, timeout=10
            )
            
            if response.status_code == 200:
                # Parse RSS feed
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'xml')
                
                items = soup.find_all('item', limit=3)
                for item in items:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    date_elem = item.find('pubDate')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text().strip()
                        link = link_elem.get_text().strip()
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        date = date_elem.get_text().strip() if date_elem else ""
                        
                        # Filter for relevance to company
                        if company_name.lower() in title.lower() or company_name.lower() in description.lower():
                            results.append({
                                'query': query,
                                'title': title,
                                'snippet': description[:200],
                                'url': link,
                                'date': date,
                                'source': 'google_news_rss'
                            })
            
            return results
            
        except Exception as e:
            if self.debug:
                print(f"    ⚠️  News feed search failed: {e}")
            return []
    
    async def _search_serpapi_free(self, query: str) -> List[Dict[str, Any]]:
        """Search using SerpAPI free tier (100 searches/month)"""
        try:
            # Note: This requires SERPAPI_API_KEY environment variable
            # Free tier: 100 searches/month
            import os
            api_key = os.getenv('SERPAPI_API_KEY')
            if not api_key:
                return []
            
            encoded_query = quote_plus(query)
            url = f"https://serpapi.com/search.json?q={encoded_query}&api_key={api_key}&num=5"
            
            response = await asyncio.to_thread(
                self.session.get, url, timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract organic results
            if data.get('organic_results'):
                for result in data['organic_results'][:5]:
                    results.append({
                        'query': query,
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'url': result.get('link', ''),
                        'date': result.get('date', ''),
                        'source': 'serpapi'
                    })
            
            return results
            
        except Exception as e:
            if self.debug:
                print(f"    ⚠️  SerpAPI search failed: {e}")
            return []
    
    async def _search_bing_free(self, query: str) -> List[Dict[str, Any]]:
        """Search using Bing Web Search API (1000 searches/month free)"""
        try:
            # Note: Requires BING_SEARCH_API_KEY
            import os
            api_key = os.getenv('BING_SEARCH_API_KEY')
            if not api_key:
                return []
            
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": api_key}
            params = {"q": query, "count": 5, "mkt": "en-US"}
            
            response = await asyncio.to_thread(
                self.session.get, url, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if data.get('webPages', {}).get('value'):
                for result in data['webPages']['value']:
                    results.append({
                        'query': query,
                        'title': result.get('name', ''),
                        'snippet': result.get('snippet', ''),
                        'url': result.get('url', ''),
                        'date': result.get('dateLastCrawled', ''),
                        'source': 'bing'
                    })
            
            return results
            
        except Exception as e:
            if self.debug:
                print(f"    ⚠️  Bing search failed: {e}")
            return []

# Alternative: Pure web scraping approach (use with caution)
class WebScrapingSearcher:
    """Web scraping based search (use responsibly)"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    async def search_company_info(self, company_name: str) -> List[Dict[str, Any]]:
        """Search by scraping news sites and company pages directly"""
        all_results = []
        
        # Search company's own newsroom/blog
        results = await self._search_company_news(company_name)
        all_results.extend(results)
        
        # Search major news sites
        news_sites = [
            "techcrunch.com",
            "reuters.com", 
            "bloomberg.com"
        ]
        
        for site in news_sites:
            try:
                results = await self._search_site_for_company(site, company_name)
                all_results.extend(results)
                await asyncio.sleep(2)  # Be respectful
            except Exception as e:
                if self.debug:
                    print(f"    ⚠️  Error searching {site}: {e}")
        
        return all_results
    
    async def _search_company_news(self, company_name: str) -> List[Dict[str, Any]]:
        """Search company's own news/blog pages"""
        domain = company_name.lower().replace(' ', '')
        potential_urls = [
            f"https://{domain}.com/news",
            f"https://{domain}.com/blog", 
            f"https://{domain}.com/press",
            f"https://blog.{domain}.com"
        ]
        
        results = []
        for url in potential_urls:
            try:
                response = await asyncio.to_thread(
                    self.session.get, url, timeout=10
                )
                if response.status_code == 200:
                    # Parse for recent news items
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for news/blog post titles
                    titles = soup.find_all(['h1', 'h2', 'h3'], limit=5)
                    for title in titles:
                        if title.get_text().strip():
                            results.append({
                                'query': f"{company_name} news",
                                'title': title.get_text().strip(),
                                'snippet': '',
                                'url': url,
                                'date': '',
                                'source': 'company_site'
                            })
                    break  # Found working news page
                    
            except Exception:
                continue
        
        return results
    
    async def _search_site_for_company(self, site: str, company_name: str) -> List[Dict[str, Any]]:
        """Search a specific news site for company mentions"""
        # This is a simplified example - real implementation would be more sophisticated
        search_url = f"https://{site}/search?q={quote_plus(company_name)}"
        
        try:
            response = await asyncio.to_thread(
                self.session.get, search_url, timeout=10
            )
            if response.status_code == 200:
                # Parse search results (simplified)
                return [{
                    'query': f"{company_name} {site}",
                    'title': f"Search results from {site}",
                    'snippet': f"Found content about {company_name}",
                    'url': search_url,
                    'date': '',
                    'source': site
                }]
        except Exception:
            pass
        
        return []