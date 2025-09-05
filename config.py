import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

#print(f"ARCADE_API_KEY (first/last 6): {os.getenv('ARCADE_API_KEY')[:6]}...{os.getenv('ARCADE_API_KEY')[-6:]}")

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
        self.arcade_api_key = self._get_env_var("ARCADE_API_KEY")
        self.openai_api_key = self._get_env_var("OPENAI_API_KEY")
    
    @staticmethod
    def _get_env_var(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Environment variable {name} is required")
        return value
