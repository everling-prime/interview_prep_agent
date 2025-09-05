from typing import List, Dict, Any
import asyncio
from arcadepy import Arcade
from email.utils import parseaddr

from models.data_models import EmailInsight, CompanyEmail
from config import Config

class EmailAnalyzer:
    """Analyzes emails from company domain to extract interview-relevant insights"""
    
    def __init__(self, config: Config, debug: bool = False):
        self.config = config
        self.client = Arcade(api_key=config.arcade_api_key)
        self.debug = debug
    
    async def analyze_company_emails(self, company_domain: str, user_id: str) -> EmailInsight:
        """
        Main method: find and analyze emails from the company
        """
        print(f"🔍 Searching for emails from {company_domain}...")
        
        # Step 1: Search for emails from company domain
        company_emails = await self._search_company_emails(company_domain, user_id)
        
        if not company_emails:
            print(f"❌ No emails found from {company_domain}")
            return EmailInsight(
                total_emails=0,
                interview_related=[],
                key_insights=[],
                important_contacts=[]
            )
        
        print(f"📧 Found {len(company_emails)} emails from {company_domain}")
        
        # Step 2: Filter for interview-relevant emails
        interview_emails = await self._filter_interview_emails(company_emails)
        print(f"🎯 {len(interview_emails)} emails identified as interview-related")
        
        # Step 3: Extract insights
        insights = self._extract_key_insights(interview_emails)
        contacts = self._extract_contacts(company_emails)
        
        return EmailInsight(
            total_emails=len(company_emails),
            interview_related=interview_emails,
            key_insights=insights,
            important_contacts=contacts
        )
    
    async def _search_company_emails(self, domain: str, user_id: str) -> List[CompanyEmail]:
        """Search Gmail using SearchThreads to filter for domain-specific emails directly"""
        try:
            if self.debug:
                print(f"🔐 Starting Gmail authorization for user: {user_id}")
            
            # Authorization
            auth_response = await asyncio.to_thread(
                self.client.auth.start,
                user_id=user_id,
                provider="google",
                scopes=["https://www.googleapis.com/auth/gmail.readonly"]
            )
            
            if self.debug:
                print(f"🔐 Auth response status: {auth_response.status}")
            
            if auth_response.status != "completed":
                print(f"🔐 Authorization required. Please visit: {auth_response.url}")
                auth_response = await asyncio.to_thread(
                    self.client.auth.wait_for_completion, 
                    auth_response
                )
                if self.debug:
                    print(f"🔐 Auth completion status: {auth_response.status}")
            
            if auth_response.status == "completed":
                print("✅ Gmail access authorized successfully")
            else:
                raise Exception(f"Authorization failed with status: {auth_response.status}")
            
            # Use Gmail.SearchThreads with sender parameter to filter by domain
            if self.debug:
                print(f"📧 Searching for threads from {domain} using Gmail SearchThreads...")
            
            result = await asyncio.to_thread(
                self.client.tools.execute,
                tool_name="Gmail.SearchThreads",  # Use SearchThreads instead of ListThreads
                user_id=user_id,
                input={"sender": f"@{domain}", "max_results": 20}  # Filter by sender domain
            )
            
            if self.debug:
                print(f"📧 SearchThreads response type: {type(result)}")
            
            # Parse the ExecuteToolResponse correctly
            if hasattr(result, 'output') and hasattr(result.output, 'value'):
                threads_data = result.output.value.get('threads', [])
                if self.debug:
                    print(f"📧 Found {len(threads_data)} threads from {domain}")
            else:
                print(f"📧 Unexpected response format: {result}")
                return []
            
            # Process the filtered threads
            company_emails = await self._process_domain_filtered_threads(threads_data, domain, user_id)
            
            if self.debug:
                if company_emails:
                    print(f"✅ Successfully found {len(company_emails)} emails from {domain}")
                else:
                    print(f"❌ No emails from {domain} found in search results")
                
            return company_emails
            
        except Exception as e:
            print(f"❌ Error in Gmail search: {str(e)}")
            print(f"❌ Error type: {type(e).__name__}")
            return []

    async def _process_domain_filtered_threads(self, threads_data: List[Dict], domain: str, user_id: str) -> List[CompanyEmail]:
        """Process threads that are already filtered by domain using SearchThreads"""
        company_emails = []
        
        if not threads_data:
            if self.debug:
                print(f"📧 No threads found for domain {domain}")
            return company_emails
        
        if self.debug:
            print(f"📧 Processing {len(threads_data)} domain-filtered threads from {domain}...")
        
        for i, thread_info in enumerate(threads_data):
            try:
                thread_id = thread_info.get('id')
                if not thread_id:
                    if self.debug:
                        print(f"⚠️  Thread {i} missing ID, skipping...")
                    continue
                
                if self.debug:
                    print(f"  📧 Processing thread {i+1}/{len(threads_data)}: {thread_id}")
                
                # Get full thread details
                thread_details = await asyncio.to_thread(
                    self.client.tools.execute,
                    tool_name="Gmail.GetThread",
                    user_id=user_id,
                    input={"thread_id": thread_id}
                )
                
                # Parse the thread details correctly
                if hasattr(thread_details, 'output') and hasattr(thread_details.output, 'value'):
                    thread_data = thread_details.output.value
                elif isinstance(thread_details, dict):
                    thread_data = thread_details
                else:
                    if self.debug:
                        print(f"    ⚠️  Unexpected thread format for {thread_id}")
                    continue
                
                # Extract email information
                sender = self._extract_sender_from_thread(thread_data)
                
                # Since SearchThreads should have filtered by domain, verify the match
                if sender and f"@{domain}" in sender.lower():
                    email = CompanyEmail(
                        id=thread_id,
                        subject=self._extract_subject_from_thread(thread_data),
                        sender=sender,
                        date=self._extract_date_from_thread(thread_data),
                        content=self._extract_content_from_thread(thread_data),
                        thread_data=thread_data
                    )
                    company_emails.append(email)
                    if self.debug:
                        print(f"    ✓ Found email from {domain}: {email.subject[:50]}...")
                else:
                    if self.debug:
                        print(f"    ⚠️  Thread sender doesn't match domain: {sender}")
                    
            except Exception as e:
                if self.debug:
                    print(f"⚠️  Error processing thread {i}: {str(e)}")
                continue
        
        return company_emails

    def _get_header(self, headers_list, name: str) -> str:
        """Helper method to extract header value from Gmail headers list"""
        if isinstance(headers_list, list):
            for h in headers_list:
                if isinstance(h, dict) and h.get("name", "").lower() == name.lower():
                    return h.get("value", "")
        return ""

    def _extract_sender_from_thread(self, thread_data: Dict) -> str:
        """Extract sender email from thread data"""
        try:
            messages = thread_data.get("messages") or []
            if messages:
                headers = messages[0].get("payload", {}).get("headers", [])
                raw_from = self._get_header(headers, "From")
                if raw_from:
                    _, addr = parseaddr(raw_from)
                    return addr or raw_from
        except Exception:
            pass

        # Fallback methods
        for field in [
            'sender', 'from', 'fromEmail', 'sender_email', 'from_email',
            'senderEmail', 'fromAddress', 'sender_address'
        ]:
            if thread_data.get(field):
                return str(thread_data[field])

        if 'messages' in thread_data and thread_data['messages']:
            first_message = thread_data['messages'][0]
            for field in [
                'sender', 'from', 'fromEmail', 'sender_email', 'from_email',
                'senderEmail', 'fromAddress', 'sender_address'
            ]:
                if first_message.get(field):
                    return str(first_message[field])

        return ""

    def _extract_subject_from_thread(self, thread_data: Dict) -> str:
        """Extract subject from thread data"""
        try:
            messages = thread_data.get("messages") or []
            if messages:
                headers = messages[0].get("payload", {}).get("headers", [])
                subj = self._get_header(headers, "Subject")
                if subj:
                    return subj
        except Exception:
            pass

        for field in ['subject', 'title', 'Subject']:
            if thread_data.get(field):
                return str(thread_data[field])

        if 'messages' in thread_data and thread_data['messages']:
            first_message = thread_data['messages'][0]
            for field in ['subject', 'title', 'Subject']:
                if first_message.get(field):
                    return str(first_message[field])

        return ""

    def _extract_date_from_thread(self, thread_data: Dict) -> str:
        """Extract date from thread data"""
        try:
            messages = thread_data.get("messages") or []
            if messages:
                msg0 = messages[0]
                internal = msg0.get("internalDate")
                if internal:
                    return str(internal)
                headers = msg0.get("payload", {}).get("headers", [])
                date_hdr = self._get_header(headers, "Date")
                if date_hdr:
                    return date_hdr
        except Exception:
            pass

        for field in ['date', 'timestamp', 'created_at', 'Date']:
            if thread_data.get(field):
                return str(thread_data[field])

        if 'messages' in thread_data and thread_data['messages']:
            first_message = thread_data['messages'][0]
            for field in ['date', 'timestamp', 'created_at', 'Date']:
                if first_message.get(field):
                    return str(first_message[field])

        return ""

    def _extract_content_from_thread(self, thread_data: Dict) -> str:
        """Extract content preview from thread data"""
        try:
            messages = thread_data.get("messages") or []
            if messages:
                msg0 = messages[0]
                if isinstance(msg0.get("snippet"), str) and msg0["snippet"]:
                    return msg0["snippet"]
                payload = msg0.get("payload", {})
                parts = payload.get("parts") or []
                for p in parts:
                    if p.get("mimeType") == "text/plain":
                        body = p.get("body", {}).get("data")
                        if isinstance(body, str) and body:
                            return body
        except Exception:
            pass

        for field in ['content', 'body', 'snippet', 'text', 'message']:
            if thread_data.get(field):
                content = thread_data[field]
                if isinstance(content, str) and content:
                    return content

        if 'messages' in thread_data and thread_data['messages']:
            first_message = thread_data['messages'][0]
            for field in ['content', 'body', 'snippet', 'text', 'message']:
                if first_message.get(field):
                    content = first_message[field]
                    if isinstance(content, str) and content:
                        return content

        return thread_data.get('snippet', '')
    
    async def _filter_interview_emails(self, emails: List[CompanyEmail]) -> List[CompanyEmail]:
        """Filter for interview-relevant emails using keyword matching"""
        interview_keywords = [
            'interview', 'hiring', 'position', 'role', 'candidate', 
            'assessment', 'onsite', 'technical', 'culture', 'team',
            'offer', 'application', 'resume', 'cv', 'background',
            'schedule', 'meeting', 'call', 'discussion', 'chat',
            'recruiter', 'recruitment', 'opportunity'
        ]
        
        relevant_emails = []
        
        for email in emails:
            content_lower = f"{email.subject} {email.content}".lower()
            
            if any(keyword in content_lower for keyword in interview_keywords):
                relevant_emails.append(email)
                if self.debug:
                    print(f"  ✓ Interview-related: {email.subject[:50]}...")
        
        return relevant_emails
    
    def _extract_key_insights(self, emails: List[CompanyEmail]) -> List[str]:
        """Extract key insights from interview-related emails"""
        insights = []
        
        for email in emails:
            content = email.content.lower()
            
            if 'engineer' in content:
                insights.append(f"Engineering role discussed in: {email.subject}")
            
            if 'process' in content or 'steps' in content:
                insights.append(f"Interview process details in: {email.subject}")
            
            if 'team' in content or 'culture' in content:
                insights.append(f"Team/culture information in: {email.subject}")
                
            if 'experience' in content or 'skills' in content:
                insights.append(f"Requirements/skills mentioned in: {email.subject}")
        
        return list(set(insights))
    
    def _extract_contacts(self, emails: List[CompanyEmail]) -> List[Dict[str, str]]:
        """Extract important contacts from company emails"""
        contacts = []
        seen_emails = set()
        
        for email in emails:
            sender_email = email.sender
            if sender_email and sender_email not in seen_emails and '@' in sender_email:
                contacts.append({
                    'email': sender_email,
                    'name': self._extract_name_from_email(sender_email),
                    'last_contact': email.date,
                    'subject': email.subject[:100] + '...' if len(email.subject) > 100 else email.subject
                })
                seen_emails.add(sender_email)
        
        return contacts[:10]
    
    @staticmethod
    def _extract_name_from_email(email: str) -> str:
        """Extract name from email address"""
        if '@' in email:
            local_part = email.split('@')[0]
            return local_part.replace('.', ' ').replace('_', ' ').replace('-', ' ').title()
        return email
