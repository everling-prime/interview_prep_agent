# agents/web_researcher.py
from typing import List, Dict, Any
import asyncio

from models.data_models import WebResearch, CompanyInfo
from config import Config

class WebResearcher:
    """Researches company online using comprehensive website scraping"""
    
    def __init__(self, config: Config, debug: bool = False):
        self.config = config
        self.debug = debug
    
    async def research_company(self, company_domain: str) -> WebResearch:
        """
        Comprehensive company research from web sources
        """
        company_name = self._domain_to_company_name(company_domain)
        print(f"🔍 Researching {company_name} ({company_domain})...")
        
        # Step 1: Skip external search - focus on comprehensive website analysis
        print(f"  🔍 Focusing on comprehensive website analysis (search disabled)")
        search_results = []
        
        # Step 2: Comprehensive website scraping
        website_content = await self._scrape_company_website(company_domain)
        
        # Step 3: Analyze and structure the research
        company_info = self._analyze_company_data(search_results, website_content)
        
        return WebResearch(
            company_domain=company_domain,
            company_name=company_name,
            search_results=search_results,
            website_content=website_content,
            structured_info=company_info
        )
    
    async def _scrape_company_website(self, domain: str) -> Dict[str, str]:
        """Lightweight website scraping for company intelligence"""
        import requests
        from bs4 import BeautifulSoup
        import time
        
        # Small, predictable set of canonical pages for a simple demo
        pages_to_scrape = [
            f"https://{domain}",           # Homepage
            f"https://{domain}/about",      # About page
            f"https://{domain}/company",    # Company page (alt)
            f"https://{domain}/careers",    # Careers page
            f"https://{domain}/blog",       # Blog (optional)
        ]
        
        scraped_content = {}
        
        # Simple browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # Limit total URL attempts per domain (not just successful scrapes)
        max_attempts = 5
        attempts = 0
        successful_scrapes = 0
        max_pages = 4  # Keep coverage lean for a demo
        
        for url in pages_to_scrape:
            if attempts >= max_attempts or successful_scrapes >= max_pages:
                break
            
            try:
                if self.debug:
                    print(f"  📄 Scraping: {url}")
                attempts += 1
                
                # Make the request with timeout
                response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                
                # Check for success status codes
                if response.status_code == 200:
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                        script.decompose()
                    
                    # Extract main content - try main first, then body
                    main_content = soup.find('main') or soup.find('body')
                    
                    if main_content:
                        # Extract text and clean it up
                        text = main_content.get_text(separator=' ', strip=True)
                        
                        # Clean up whitespace and limit length
                        text = ' '.join(text.split())
                        content_limit = 2000 if any(page in url for page in ['/about', '/company']) else 1500
                        text = text[:content_limit]
                        
                        if text and len(text) > 100:  # Ensure we got meaningful content
                            page_name = url.split('/')[-1] or 'home'
                            scraped_content[page_name] = text
                            successful_scrapes += 1
                            
                            if self.debug:
                                print(f"    ✓ Scraped {len(text)} characters")
                        else:
                            if self.debug:
                                print(f"    ⚠️  Insufficient content found for {url}")
                
                elif response.status_code == 404:
                    if self.debug:
                        print(f"    ⚠️  Page not found: {url} (404) - trying next page")
                    continue  # Try next URL instead of failing
                    
                else:
                    if self.debug:
                        print(f"    ⚠️  HTTP {response.status_code} for {url} - trying next page")
                    continue
                
                # Be respectful - add delay between requests
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                if self.debug:
                    print(f"    ⚠️  Network error for {url}: {str(e)} - trying next page")
                continue  # Try next URL instead of failing
                
            except Exception as e:
                if self.debug:
                    print(f"    ⚠️  Error parsing {url}: {str(e)} - trying next page")
                continue  # Try next URL instead of failing
        
        print(f"🌐 Scraped {len(scraped_content)} pages successfully")
        return scraped_content
    
    def _analyze_company_data(self, search_results: List[Dict], website_content: Dict[str, str]) -> CompanyInfo:
        """Analyze and structure company information"""
        # Extract key information from search results (will be empty now)
        recent_news = []
        for result in search_results[:10]:
            if result.get('title') and result.get('snippet'):
                recent_news.append(f"{result['title']}: {result['snippet']}")
        
        return CompanyInfo(
            mission=website_content.get('about', '')[:500] or website_content.get('home', '')[:500],
            recent_news=recent_news
        )
    
    @staticmethod
    def _domain_to_company_name(domain: str) -> str:
        """Convert domain to likely company name"""
        # Remove common TLDs and subdomains
        name = domain.replace('.com', '').replace('.org', '').replace('.net', '')
        name = name.replace('www.', '')
        return name.replace('-', ' ').replace('_', ' ').title()
