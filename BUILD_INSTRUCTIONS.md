# Complete Setup Instructions - Interview Prep Agent

## Overview

This document provides complete step-by-step instructions to recreate the Interview Prep Agent project from scratch. This AI-powered agent analyzes email communications and researches company websites to generate tailored interview preparation reports.

## Prerequisites

### Required Software
- **Python 3.13+** - The project requires Python 3.13 or newer
- **Git** - For cloning and version control
- **uv** (recommended) or **pip** - Python package manager

### Required API Keys
- **Arcade API Key** - For Gmail access and Google Docs creation
- **OpenAI API Key** - For AI-powered report generation

## Step 1: Environment Setup

### Install Python 3.13+
```bash
# macOS (using Homebrew)
brew install python@3.13

# Ubuntu/Debian
sudo apt update
sudo apt install python3.13 python3.13-venv

# Windows
# Download from python.org
```

### Install uv (Recommended Package Manager)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: using pip
pip install uv
```

## Step 2: Project Setup

### Create Project Directory
```bash
mkdir interview_prep_agent
cd interview_prep_agent
```

### Initialize Git Repository
```bash
git init
```

### Create Project Structure
```bash
# Create main directories
mkdir -p agents
mkdir -p models
mkdir -p output/prep_reports
mkdir -p scripts
mkdir -p .claude

# Create __init__.py files for Python modules
touch agents/__init__.py
touch models/__init__.py

# Create output placeholder
touch output/prep_reports/.gitkeep
```

## Step 3: Configuration Files

### Create pyproject.toml
```toml
[project]
name = "interview-prep-agent"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "arcadepy>=1.7.0",
    "beautifulsoup4>=4.13.5",
    "openai>=1.105.0",
    "python-dotenv>=1.1.1",
    "requests>=2.32.5",
]
```

### Create .env.example
```bash
ARCADE_API_KEY=your_arcade_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Create .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Output files
output/
!output/.gitkeep
!output/prep_reports/.gitkeep

# Archive
archive_unused/

# IDE
.vscode/
.idea/
*.swp
*.swo

# macOS
.DS_Store
```

## Step 4: Core Application Files

### Create config.py
```python
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
        self.arcade_api_key = self._get_env_var("ARCADE_API_KEY")
        self.openai_api_key = self._get_env_var("OPENAI_API_KEY")
    
    @staticmethod
    def _get_env_var(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Environment variable {name} is required")
        return value
```

### Create models/data_models.py
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class EmailInsight:
    """Represents insights from email analysis"""
    total_emails: int
    interview_related: List[Dict[str, Any]]
    key_people: List[str]
    communication_timeline: List[Dict[str, Any]]
    summary: str

@dataclass
class WebResearch:
    """Represents web research findings"""
    company_info: Dict[str, Any]
    key_pages_analyzed: List[str]
    summary: str
    
@dataclass
class PrepReport:
    """Complete interview prep report"""
    company_domain: str
    generated_at: datetime
    email_insights: Optional[EmailInsight]
    web_research: Optional[WebResearch]
    final_report: str
```

### Create main.py (Basic Structure)
```python
#!/usr/bin/env python3
"""
Interview Prep Coach Agent
Usage: python main.py --company stripe.com --user-id your@email.com
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.email_analyzer import EmailAnalyzer
    from agents.web_researcher import WebResearcher
    from agents.prep_coach import PrepCoach
    from config import Config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have all the required files:")
    print("   - config.py")
    print("   - agents/email_analyzer.py")
    print("   - agents/web_researcher.py")
    print("   - agents/prep_coach.py")
    print("   - models/data_models.py")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Interview Prep Coach Agent")
    parser.add_argument("--company", required=True, help="Company domain (e.g., stripe.com)")
    parser.add_argument("--user-id", required=True, help="Your email address")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--email-only", action="store_true", help="Skip web research")
    parser.add_argument("--save-to-docs", action="store_true", help="Save to Google Docs")
    parser.add_argument("--docs-only", action="store_true", help="Only save to docs, not local")
    parser.add_argument("--output-dir", default="output/prep_reports", help="Output directory")
    
    args = parser.parse_args()
    
    try:
        config = Config()
        # Initialize agents and run the main logic here
        print(f"🚀 Starting interview prep for {args.company}")
        # Implementation would go here
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Step 5: Agent Implementations

### Create agents/email_analyzer.py (Skeleton)
```python
"""Email analysis agent using Arcade Gmail tools"""
from typing import Optional
from models.data_models import EmailInsight
from config import Config

class EmailAnalyzer:
    def __init__(self, config: Config):
        self.config = config
    
    async def analyze_company_emails(self, company_domain: str, user_id: str) -> Optional[EmailInsight]:
        """Analyze emails from a specific company domain"""
        # Implementation using Arcade Gmail tools
        pass
```

### Create agents/web_researcher.py (Skeleton)
```python
"""Web research agent for company information"""
from typing import Optional
from models.data_models import WebResearch
from config import Config

class WebResearcher:
    def __init__(self, config: Config):
        self.config = config
    
    async def research_company(self, company_domain: str) -> Optional[WebResearch]:
        """Research company information from web"""
        # Implementation using web scraping
        pass
```

### Create agents/prep_coach.py (Skeleton)
```python
"""Interview prep coaching agent using OpenAI"""
from typing import Optional
from models.data_models import EmailInsight, WebResearch
from config import Config

class PrepCoach:
    def __init__(self, config: Config):
        self.config = config
    
    async def generate_prep_report(self, company_domain: str, email_insights: Optional[EmailInsight], 
                                 web_research: Optional[WebResearch]) -> str:
        """Generate interview preparation report"""
        # Implementation using OpenAI
        pass
```

## Step 6: Scripts and Utilities

### Create scripts/demo.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

# Simple demo runner for Interview Prep Agent
# Usage: scripts/demo.sh <company_domain> <user_email> [--debug] [--save-to-docs]

company=${1:-"arcade.dev"}
user_id=${2:-"you@example.com"}
shift 2 || true

extra_args=${*:-}

echo "Running demo for company: $company"
echo "User ID: $user_id"

if ! command -v uv >/dev/null 2>&1; then
  echo "Note: 'uv' not found. Falling back to python from current environment." >&2
  python main.py --company "$company" --user-id "$user_id" $extra_args
else
  uv run python main.py --company "$company" --user-id "$user_id" $extra_args
fi
```

### Make demo script executable
```bash
chmod +x scripts/demo.sh
```

## Step 7: Environment Configuration

### Set up environment variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual API keys
# ARCADE_API_KEY=your_actual_arcade_key
# OPENAI_API_KEY=your_actual_openai_key
```

## Step 8: Install Dependencies

### Using uv (Recommended)
```bash
uv sync
```

### Using pip (Alternative)
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install arcadepy>=1.7.0 beautifulsoup4>=4.13.5 openai>=1.105.0 python-dotenv>=1.1.1 requests>=2.32.5
```

## Step 9: Test the Setup

### Basic test
```bash
# Test with uv
uv run python main.py --company test.com --user-id test@example.com

# Test with standard Python
source .venv/bin/activate
python main.py --company test.com --user-id test@example.com
```

### Test with demo script
```bash
bash scripts/demo.sh arcade.dev you@example.com --debug
```

## Step 10: API Key Setup

### Get Arcade API Key
1. Visit https://arcade.dev
2. Sign up for an account
3. Navigate to API keys section
4. Generate a new API key
5. Add to your `.env` file

### Get OpenAI API Key
1. Visit https://platform.openai.com
2. Sign up or log in
3. Navigate to API keys
4. Create a new API key
5. Add to your `.env` file

## Step 11: Optional — Add Arcade Docs to Your AI IDE (Context7 MCP)

If your AI IDE supports the Model Context Protocol (MCP), you can add the Context7 MCP so your assistant can reference the latest arcade.dev documentation directly inside your IDE.

What you’ll need:
- An IDE or assistant that supports MCP (e.g., many AI IDEs/assistants now support adding MCP servers).
- The Context7 MCP server installed (follow the Context7 installation guide for your OS).
- A Context7 account/API key if required by your setup.

Setup steps:
1. Install the Context7 MCP server using the official installer or package for your platform.
2. Open your AI IDE’s MCP configuration and add a new server entry for Context7.
3. Provide the command/path to the Context7 MCP server binary and, if applicable, set `CONTEXT7_API_KEY` in the server’s environment.
4. In the Context7 configuration, add/select the Arcade documentation source so queries include `arcade.dev` docs.
5. Restart your IDE/assistant and test by asking a docs question (e.g., “Show Arcade Gmail tools capabilities”).

Example (generic MCP client config):
```json
{
  "mcpServers": {
    "context7": {
      "command": "/path/to/context7-mcp", 
      "args": [],
      "env": {
        "CONTEXT7_API_KEY": "your_context7_api_key_if_required"
      },
      "disabled": false
    }
  }
}
```

Notes:
- Exact install commands, binary names, and config file locations vary by IDE. Refer to your IDE’s MCP docs and the Context7 setup guide for precise steps.
- Ensure you explicitly enable the Arcade docs/library/source within Context7 so your assistant can reference `arcade.dev` documentation.
- You can disable or remove the MCP server anytime from your IDE’s settings.

## Project Structure Overview

After following these instructions, your project structure should look like:

```
interview_prep_agent/
├── .env                          # Environment variables (not committed)
├── .env.example                  # Example environment file
├── .gitignore                    # Git ignore rules
├── README.md                     # Project documentation
├── SETUP_INSTRUCTIONS.md         # This file
├── config.py                     # Configuration management
├── main.py                       # Main entry point
├── pyproject.toml               # Project dependencies
├── uv.lock                      # Dependency lock file (generated)
├── agents/                      # AI agents
│   ├── __init__.py
│   ├── email_analyzer.py        # Email analysis agent
│   ├── prep_coach.py           # Interview prep coach
│   └── web_researcher.py       # Web research agent
├── models/                      # Data models
│   ├── __init__.py
│   └── data_models.py          # Data structures
├── output/                      # Generated reports
│   └── prep_reports/           # Interview prep reports
│       └── .gitkeep           # Placeholder file
└── scripts/                     # Utility scripts
    └── demo.sh                 # Demo runner script
```

## Usage Examples

Once set up, you can use the agent with commands like:

```bash
# Basic usage
uv run python main.py --company stripe.com --user-id your@email.com

# With debug logging
uv run python main.py --company openai.com --user-id you@example.com --debug

# Save to Google Docs
uv run python main.py --company stripe.com --user-id you@example.com --save-to-docs

# Using the demo script
bash scripts/demo.sh arcade.dev you@example.com --debug
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Missing API Keys**: Check that your `.env` file has both required keys
3. **Python Version**: Verify you're using Python 3.13+
4. **Dependencies**: Run `uv sync` to install all required packages

### Getting Help

- Check the README.md for usage examples
- Verify all files are created as specified
- Ensure environment variables are properly set
- Test with the demo script first

## Next Steps

1. Implement the full logic in the agent classes
2. Add comprehensive error handling
3. Expand web research capabilities
4. Add more output formats
5. Implement proper logging
6. Add unit tests

This setup provides the complete foundation for the Interview Prep Agent project.
