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
    
    # Show intelligent email decisions
    if email_insights and email_insights.interview_related:
        print(f"📧 EMAIL INTELLIGENCE:")
        print(f"   Found {email_insights.total_emails} total emails from company")
        print(f"   ✨ Agent identified {len(email_insights.interview_related)} as interview-relevant")
        print(f"   🎯 Key insight: Agent prioritized hiring communication over routine emails")
    elif email_insights and email_insights.total_emails > 0:
        print(f"📧 EMAIL INTELLIGENCE:")
        print(f"   Found {email_insights.total_emails} total emails from company")
        print(f"   ✨ Agent analyzed content but found no interview-specific communications")
        print(f"   🎯 Shows intelligent filtering - job alerts ≠ interview communications")
    
    if web_research:
        # Show web research intelligence
        print(f"\n🔍 WEB RESEARCH INTELLIGENCE:")
        search_count = len(web_research.search_results) if web_research.search_results else 0
        website_count = len(web_research.website_content) if web_research.website_content else 0
        print(f"   Executed strategic search queries")
        print(f"   📊 Gathered {search_count} relevant search results")
        print(f"   🌐 Scraped {website_count} key company pages")
        print(f"   ✨ Agent focused on recent news and culture for interview relevance")
    
    print(f"\n🧠 AI SYNTHESIS INTELLIGENCE:")
    print(f"   ✨ Agent acting as expert interview coach with 20+ years experience")
    print(f"   🎯 Connecting email context with company intelligence using AI")
    print(f"   📝 Creating personalized coaching advice, not generic templates")
    print(f"   🤖 OpenAI GPT analyzing patterns and generating strategic recommendations")
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
        email_analyzer = EmailAnalyzer(config)
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
            prep_report = create_fallback_report(args.company, email_insights, web_research)
        
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
            print(f"🔍 Web Research: {len(web_research.search_results)} search results, {len(web_research.website_content)} pages scraped")
        
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

def create_fallback_report(company: str, email_insights, web_research=None) -> str:
    """Create a basic fallback report if AI coaching fails"""
    report = f"""# Interview Prep Report - {company.upper()}
*Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*
*AI coaching unavailable - basic analysis provided*

## Executive Summary

Based on analysis of {email_insights.total_emails} emails and {len(web_research.search_results) if web_research else 0} research sources for {company}.

## Email Analysis Results

- **Total emails analyzed**: {email_insights.total_emails}
- **Interview-relevant emails**: {len(email_insights.interview_related)}
- **Key contacts identified**: {len(email_insights.important_contacts)}

"""
    
    # Add key findings
    if email_insights.interview_related:
        report += "## Interview Communications Found\n\n"
        for email in email_insights.interview_related[:3]:
            report += f"- **{email.get('subject', 'N/A')}** from {email.get('sender', 'N/A')}\n"
    else:
        report += "## No Direct Interview Communications\n\nConsider reaching out to confirm interview process details.\n\n"
    
    # Add web research if available
    if web_research and web_research.search_results:
        report += "## Recent Company News\n\n"
        for result in web_research.search_results[:5]:
            if result.get('title') and result.get('snippet'):
                report += f"- **{result['title']}**\n"
                report += f"  {result['snippet'][:100]}...\n\n"
    
    # Add contacts
    if email_insights.important_contacts:
        report += "## Key Contacts\n\n"
        for contact in email_insights.important_contacts[:3]:
            # Handle both dict and object formats for contacts
            if hasattr(contact, 'get'):
                name = contact.get('name', 'Unknown')
                subject = contact.get('subject', 'N/A')
            else:
                name = getattr(contact, 'name', getattr(contact, 'email', 'Unknown'))
                subject = getattr(contact, 'subject', 'N/A')
            report += f"- **{name}** - {subject}\n"
    
    report += """
## Basic Recommendations

1. Review the communications above for process details
2. Research the company's recent developments mentioned
3. Prepare specific examples that align with company values
4. Follow up on any pending communications

*For detailed AI-powered insights, please check your OpenAI API configuration.*
"""
    
    return report

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