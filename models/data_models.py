from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class CompanyEmail:
    """Represents an email from the target company"""
    id: str
    subject: str
    sender: str
    date: str
    content: str
    thread_data: Dict[str, Any]

@dataclass
class EmailInsight:
    """Insights extracted from company emails"""
    total_emails: int
    interview_related: List[CompanyEmail]
    key_insights: List[str]
    important_contacts: List[Dict[str, str]]

@dataclass
class CompanyInfo:
    """Structured company information"""
    mission: str
    recent_news: List[str]

@dataclass
class WebResearch:
    """Web research results"""
    company_domain: str
    company_name: str
    search_results: List[Dict[str, Any]]
    website_content: Dict[str, str]
    structured_info: CompanyInfo