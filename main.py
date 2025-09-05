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

def print_demo_highlights(email_insights, web_research=None):
    """Print key highlights for demo purposes"""
    print("\n" + "🎯 AGENTIC INTELLIGENCE HIGHLIGHTS" + "\n" + "=" * 50)
    
    # Email intelligence summary
    if email_insights:
        interview_count = len(email_insights.interview_related) if email_insights.interview_related else 0
        print(f"📧 EMAIL: Found {email_insights.total_emails} emails, {interview_count} interview-relevant")
        if interview_count > 0:
            print(f"   ✨ Agent intelligently filtered hiring communications from routine emails")
    
    # Web research summary  
    if web_research:
        website_count = len(web_research.website_content) if web_research.website_content else 0
        print(f"🔍 WEB: Scraped {website_count} key company pages (about, careers, blog)")
    
    # AI synthesis summary
    print(f"🧠 AI: Expert interview coach synthesizing personalized recommendations")
    print("=" * 50)

async def main():
    parser = argparse.ArgumentParser(
        description='Interview Prep Coach Agent - AI-powered interview preparation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --company stripe.com --user-id john@example.com
  python main.py --company linkedin.com --user-id jane@example.com --output-dir ./reports
  python main.py --company openai.com --user-id user@example.com --save-to-docs
        """
    )
    parser.add_argument('--company', required=True, 
                       help='Company domain (e.g., stripe.com)')
    parser.add_argument('--user-id', required=True,
                       help='Your email address for Arcade authentication')
    parser.add_argument('--output-dir', default='output/prep_reports',
                       help='Output directory for prep reports')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with detailed logging')
    parser.add_argument('--email-only', action='store_true',
                       help='Only analyze emails, skip web research')
    parser.add_argument('--save-to-docs', action='store_true',
                       help='Save the report to Google Docs (requires Google authentication)')
    parser.add_argument('--docs-only', action='store_true',
                       help='Only save to Google Docs, skip local file creation')
    
    args = parser.parse_args()
    
    print("🎯 Interview Prep Coach Agent")
    print("=" * 50)
    print(f"Company: {args.company}")
    print(f"User: {args.user_id}")
    if args.save_to_docs or args.docs_only:
        print("📄 Google Docs integration: ENABLED")
    print("=" * 50)
    
    try:
        # Initialize configuration and components
        print("⚙️  Initializing configuration...")
        config = Config()
        email_analyzer = EmailAnalyzer(config, debug=args.debug)
        web_researcher = WebResearcher(config, debug=args.debug)
        
        # Step 1: Analyze emails from company
        print("\n📧 Phase 1: Analyzing email communications...")
        email_insights = await email_analyzer.analyze_company_emails(
            args.company, args.user_id
        )
        
        if args.debug:
            print(f"🐛 Debug: Email insights: {email_insights}")
        
        # Step 2: Research company online (unless --email-only)
        web_research = None
        if not args.email_only:
            print(f"\n🔍 Phase 2: Researching company intelligence...")
            web_research = await web_researcher.research_company(args.company)
            
            if args.debug:
                print(f"🐛 Debug: Web research results: {len(web_research.search_results)} search results, {len(web_research.website_content)} pages scraped")
        
        # Show demo highlights
        print_demo_highlights(email_insights, web_research)
        
        # Step 3: Generate AI-powered interview prep report
        print(f"\n🧠 Phase 3: Creating AI-powered interview prep report...")
        prep_coach = PrepCoach(config, debug=args.debug)
        
        try:
            # Use AI PrepCoach to generate intelligent report
            prep_report = await prep_coach.create_prep_report(
                company=args.company,
                email_insights=email_insights,
                web_research=web_research
            )
        except Exception as e:
            print(f"⚠️  AI coach unavailable ({str(e)}), falling back to basic report...")
            # Fallback to basic report if OpenAI fails
            prep_report = prep_coach._create_fallback_report(args.company, email_insights, web_research)
        
        # Step 4: Save the report
        doc_info = None
        local_path = None
        
        # Save to Google Docs if requested
        if args.save_to_docs or args.docs_only:
            print(f"\n📄 Phase 4a: Saving report to Google Docs...")
            try:
                doc_info = await prep_coach.save_to_google_docs(args.company, prep_report, args.user_id)
                print(f"✅ Google Doc created: {doc_info['title']}")
                if 'url' in doc_info:
                    print(f"🔗 Google Doc URL: {doc_info['url']}")
            except Exception as e:
                print(f"❌ Failed to save to Google Docs: {str(e)}")
                print("💡 Falling back to local file...")
                args.docs_only = False  # Force local save as fallback
        
        # Save to local file (unless docs-only mode and Google Docs succeeded)
        if not args.docs_only or doc_info is None:
            print(f"\n📄 Phase 4b: Saving report to local file...")
            local_path = save_report(args.company, prep_report, args.output_dir)
        
        # Success summary
        print("\n" + "=" * 50)
        print("✅ Interview Prep Analysis Complete!")
        print(f"📊 Email Analysis: {email_insights.total_emails} total emails, {len(email_insights.interview_related)} interview-related")
        if web_research:
            print(f"🔍 Web Research: {len(web_research.website_content)} pages scraped")
        
        # Report location info
        if doc_info and 'url' in doc_info:
            print(f"📄 Google Doc: {doc_info['url']}")
        if local_path:
            print(f"📄 Local file: {local_path}")
        print("=" * 50)
        
        # Show preview of report
        print("\n📋 Report Preview:")
        print("-" * 30)
        preview = prep_report[:500] + "..." if len(prep_report) > 500 else prep_report
        print(preview)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        else:
            print("💡 Use --debug flag for detailed error information")
            print("💡 Check your API keys and internet connection")
            print("💡 For Google Docs integration, ensure you have proper authentication")
        return 1

## Deprecated fallback removed; use PrepCoach._create_fallback_report

def save_report(company: str, report: str, output_dir: str) -> str:
    """Save the prep report to a file"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{company.replace('.', '_')}_prep_{timestamp}.md"
    filepath = Path(output_dir) / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return str(filepath)

if __name__ == "__main__":
    exit(asyncio.run(main()))
