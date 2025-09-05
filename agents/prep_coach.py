# agents/prep_coach.py
import openai
from typing import Dict, Any, Optional
import asyncio

from models.data_models import EmailInsight, WebResearch
from config import Config

# Import Arcade client for Google Docs integration
try:
    from arcadepy import Arcade
except ImportError:
    Arcade = None
    print("⚠️  Arcade SDK not available - install with 'pip install arcadepy'")

class PrepCoach:
    """AI-powered interview coach that synthesizes research into actionable advice"""
    
    def __init__(self, config: Config, debug: bool = False):
        self.config = config
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        self.debug = debug
        self.arcade_client = Arcade(api_key=config.arcade_api_key) if Arcade else None
    
    async def create_prep_report(self, company: str, email_insights: EmailInsight, 
                               web_research: Optional[WebResearch] = None) -> str:
        """
        Create comprehensive interview preparation report using OpenAI
        """
        if self.debug:
            print("🧠 Generating interview prep report with AI coach...")
        
        coach_prompt = self._build_coach_prompt(company, email_insights, web_research)
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert executive interview coach with 20 years of experience helping candidates succeed at top technology companies. You provide specific, actionable advice based on research and communication history. Always be specific and personalized rather than generic."
                    },
                    {
                        "role": "user", 
                        "content": coach_prompt
                    }
                ],
                max_tokens=self.config.max_tokens,
                temperature=0.7
            )
            
            report = response.choices[0].message.content
            if self.debug:
                print("✅ Interview prep report generated successfully!")
            return report
            
        except Exception as e:
            error_msg = f"❌ Error generating prep report: {str(e)}"
            print(error_msg)
            # Return a fallback basic report
            return self._create_fallback_report(company, email_insights, web_research)
    
    async def save_to_google_docs(self, company: str, report_content: str, user_id: str) -> Dict[str, Any]:
        """
        Save the interview prep report to a new Google Doc using Arcade's GoogleDocs toolkit
        Returns document information including URL if available
        
        Args:
            company: Company name for the report
            report_content: The full report content to save
            user_id: User ID for Arcade authentication (typically email address)
        """
        if not self.arcade_client:
            raise Exception("Arcade SDK not available. Install with 'pip install arcadepy'")
        
        if self.debug:
            print("📄 Creating Google Doc with interview prep report using Arcade...")
        
        try:
            # Create a descriptive title with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            doc_title = f"Interview Prep Report - {company.upper()} - {timestamp}"
            
            if self.debug:
                print(f"🔧 Creating document with title: {doc_title}")
            
            # Use Arcade's GoogleDocs CreateDocumentFromText tool directly for simplicity
            full_tool_name = "GoogleDocs.CreateDocumentFromText"
            if self.debug:
                print(f"🔧 Using GoogleDocs tool: {full_tool_name}")
            
            # Authorize the tool for the user
            auth_result = await asyncio.to_thread(
                self.arcade_client.tools.authorize,
                tool_name=full_tool_name,
                user_id=user_id
            )
            
            if self.debug:
                print(f"🔧 Authorization result: {auth_result}")
            
            # Wait for authorization completion if needed
            if hasattr(auth_result, 'status') and auth_result.status == 'pending':
                if self.debug:
                    print("🔧 Waiting for authorization completion...")
                await asyncio.to_thread(
                    self.arcade_client.auth.wait_for_completion,
                    auth_result
                )
            
            # Execute the tool to create the document
            execution_result = await asyncio.to_thread(
                self.arcade_client.tools.execute,
                tool_name=full_tool_name,
                input={
                    "title": doc_title,
                    "text_content": report_content
                },
                user_id=user_id
            )
            
            if self.debug:
                print(f"✅ Google Doc created successfully: {doc_title}")
            
            # Return the document info
            doc_info = {
                "title": doc_title,
                "result": execution_result,
                "timestamp": timestamp,
                "tool_used": full_tool_name
            }
            
            # Try to extract document ID and URL from the result
            if hasattr(execution_result, 'output') and execution_result.output:
                output = execution_result.output
                if isinstance(output, dict):
                    doc_id = (
                        output.get('documentId') or
                        output.get('document_id') or
                        output.get('id')
                    )
                    if doc_id:
                        doc_info["document_id"] = doc_id
                        doc_info["url"] = f"https://docs.google.com/document/d/{doc_id}/edit"
                elif isinstance(output, str) and "docs.google.com" in output:
                    doc_info["url"] = output
            
            # Also check if the result itself contains the document info
            if hasattr(execution_result, 'documentId'):
                doc_info["document_id"] = execution_result.documentId
                doc_info["url"] = f"https://docs.google.com/document/d/{execution_result.documentId}/edit"
            elif hasattr(execution_result, 'id'):
                doc_info["document_id"] = execution_result.id
                doc_info["url"] = f"https://docs.google.com/document/d/{execution_result.id}/edit"
            
            return doc_info
            
        except Exception as e:
            error_msg = f"❌ Error creating Google Doc with Arcade: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _build_coach_prompt(self, company: str, email_insights: EmailInsight, 
                           web_research: Optional[WebResearch] = None) -> str:
        """Build the comprehensive coaching prompt for OpenAI"""
        
        # Format email insights
        email_summary = self._format_email_insights(email_insights)
        
        # Format web research
        web_summary = self._format_web_research(web_research)
        
        prompt = f"""# Interview Preparation Analysis for {company.upper()}

I'm analyzing communication and research data for a candidate interviewing at {company}. Create a comprehensive, personalized interview preparation report.

## Email Communication Analysis
- Total emails from company: {email_insights.total_emails}
- Interview-related emails: {len(email_insights.interview_related)}
- Key contacts identified: {len(email_insights.important_contacts)}

### Email Communication Details:
{email_summary}

## Company Research Results
{web_summary}

---

# Create a Comprehensive Interview Prep Report

Structure your response as a professional interview preparation document with these sections:

## 1. Executive Summary
- What this specific company values based on the research
- Key themes from their communication patterns
- Strategic positioning advice for this candidate

## 2. Company Intelligence Brief
- Recent developments and strategic priorities (from research)
- Company culture and values assessment
- Key products/services the candidate should understand deeply

## 3. Interview Process Analysis
- Evaluation criteria based on communication patterns
- Skills/experiences this company has emphasized
- Interview format expectations (if discoverable)

## 4. Strategic Preparation Recommendations
- Top 3 specific things to emphasize about background
- 5 likely interview questions with tailored approach strategies
- Company-specific talking points to weave into answers
- Intelligent questions to ask that demonstrate genuine research

## 5. Relationship & Communication Context
- Key contacts and their roles/importance
- How to appropriately reference previous communications
- Networking and follow-up opportunities

## 6. Day-of-Interview Tactical Advice
- Specific preparation checklist for this company
- Key messages to reinforce throughout the conversation
- Follow-up strategy recommendations

Make this highly specific to {company} and this candidate's situation. Use actual data points from the research and communication history. Avoid generic interview advice - focus on what makes this company and situation unique."""

        return prompt
    
    def _format_email_insights(self, email_insights: EmailInsight) -> str:
        """Format email insights for the prompt"""
        if email_insights.total_emails == 0:
            return "No email communications found with this company."
        
        insights = []
        
        # Interview-related emails
        if email_insights.interview_related:
            insights.append("**Interview-Related Communications:**")
            for email in email_insights.interview_related[:3]:  # Limit for prompt length
                # Use direct attribute access for CompanyEmail objects
                subject = getattr(email, 'subject', 'N/A')
                content = getattr(email, 'content', getattr(email, 'snippet', 'N/A'))
                insights.append(f"- Subject: '{subject}' - {content[:150]}...")
        
        # Key contacts
        if email_insights.important_contacts:
            insights.append("\n**Key Company Contacts:**")
            for contact in email_insights.important_contacts[:3]:
                # Handle both dict and object formats
                if hasattr(contact, 'get'):
                    name = contact.get('name', 'Unknown')
                    subject = contact.get('subject', 'N/A')
                else:
                    name = getattr(contact, 'name', getattr(contact, 'email', 'Unknown'))
                    subject = getattr(contact, 'subject', 'N/A')
                insights.append(f"- {name}: Last contact about '{subject}'")
        
        # General insights
        if email_insights.key_insights:
            insights.append("\n**Communication Patterns:**")
            for insight in email_insights.key_insights[:3]:
                insights.append(f"- {insight}")
        
        return "\n".join(insights) if insights else "Limited email communication data available."
    
    def _format_web_research(self, web_research: Optional[WebResearch]) -> str:
        """Format web research for the prompt"""
        if not web_research:
            return "Limited company research data available."
        summary = []
        
        # Search results summary
        if web_research.search_results:
            summary.append(f"**Recent News & Information ({len(web_research.search_results)} sources):**")
            for result in web_research.search_results[:5]:  # Top 5 most relevant
                title = result.get('title', 'N/A')
                snippet = result.get('snippet', 'N/A')
                summary.append(f"- {title}: {snippet[:100]}...")
        
        # Website content
        if web_research.website_content:
            summary.append(f"\n**Company Website Analysis ({len(web_research.website_content)} pages):**")
            for page, content in web_research.website_content.items():
                summary.append(f"- {page.title()} page: {content[:150]}...")
        
        # Structured info
        if web_research.structured_info and web_research.structured_info.recent_developments:
            summary.append(f"\n**Key Recent Developments:**")
            for dev in web_research.structured_info.recent_developments[:3]:
                summary.append(f"- {dev[:100]}...")
        
        return "\n".join(summary) if summary else "Limited company research data available."
    
    def _create_fallback_report(self, company: str, email_insights: EmailInsight, 
                              web_research: Optional[WebResearch] = None) -> str:
        """Create a basic fallback report if OpenAI fails"""
        search_sources_count = len(web_research.search_results) if (web_research and web_research.search_results) else 0
        website_pages_count = len(web_research.website_content) if (web_research and web_research.website_content) else 0
        return f"""# Interview Preparation Report - {company.upper()}
*AI-generated report unavailable - basic analysis provided*

## Summary
Based on analysis of {email_insights.total_emails} emails and {search_sources_count} research sources for {company}.

## Email Analysis
- Total communications: {email_insights.total_emails}
- Interview-related: {len(email_insights.interview_related)}
- Key contacts: {len(email_insights.important_contacts)}

## Research Findings
- Search results analyzed: {search_sources_count}
- Website pages reviewed: {website_pages_count}

## Recommendations
1. Review the email communications for process details
2. Research the key contacts identified in your communications
3. Study the recent news and developments found in web research
4. Prepare specific examples that align with company values discovered

*For detailed AI-powered insights, please check your OpenAI API configuration.*
"""
