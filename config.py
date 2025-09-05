import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Configuration for the Interview Prep Agent"""
    
    # API Keys
    arcade_api_key: str
    openai_api_key: str
    
    # Arcade settings
    arcade_base_url: str = "https://api.arcade.dev"
    
    # Analysis settings
    email_lookback_days: int = 90  # 3 months
    max_emails_to_analyze: int = 50
    max_search_results: int = 10
    
    # OpenAI settings
    openai_model: str = "gpt-4o-mini"  # Cost-effective choice
    max_tokens: int = 2000
    
    def __init__(self):
        self.arcade_api_key = os.getenv("ARCADE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.arcade_api_key:
            raise ValueError("ARCADE_API_KEY environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
