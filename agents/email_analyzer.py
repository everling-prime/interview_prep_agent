from typing import List, Dict, Any
import asyncio
from email.utils import parseaddr
import openai

from models.data_models import EmailInsight, CompanyEmail
from config import Config
from tools.gmail import GmailTool
from utils.logging import EventLogger


def _extract_header(thread_data: Dict, name: str) -> str:
    try:
        messages = thread_data.get("messages") or []
        if messages:
            headers = messages[0].get("payload", {}).get("headers", [])
            if isinstance(headers, list):
                for h in headers:
                    if isinstance(h, dict) and h.get("name", "").lower() == name.lower():
                        return h.get("value", "")
    except Exception:
        pass
    return ""


def _extract_sender_from_thread(thread_data: Dict) -> str:
    try:
        messages = thread_data.get("messages") or []
        if messages:
            raw_from = _extract_header(thread_data, "From")
            if raw_from:
                _, addr = parseaddr(raw_from)
                return addr or raw_from
    except Exception:
        pass
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


def _extract_subject_from_thread(thread_data: Dict) -> str:
    try:
        messages = thread_data.get("messages") or []
        if messages:
            subj = _extract_header(thread_data, "Subject")
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


def _extract_content_from_thread(thread_data: Dict) -> str:
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


class EmailAnalyzer:
    """LLM-based analyzer that uses Gmail via Arcade tools and GPT extraction."""

    def __init__(self, config: Config, gmail: GmailTool, logger: EventLogger | None = None, debug: bool = False):
        self.config = config
        self.gmail = gmail
        self.debug = debug
        self.logger = logger or EventLogger()
        self.openai = openai.OpenAI(api_key=config.openai_api_key)

    async def analyze_company_emails(self, company_domain: str, user_id: str) -> EmailInsight:
        # Search threads by domain
        threads = await self.gmail.search_threads(company_domain, user_id=user_id, max_results=self.config.max_emails_to_analyze)
        if not threads:
            return EmailInsight(total_emails=0, interview_related=[], key_insights=[], important_contacts=[])

        detailed: List[Dict[str, Any]] = []
        for th in threads[: self.config.max_emails_to_analyze]:
            tid = th.get('id')
            if not tid:
                continue
            td = await self.gmail.get_thread(tid, user_id=user_id)
            detailed.append(td)

        compact = [
            {
                "id": d.get("id"),
                "subject": _extract_subject_from_thread(d),
                "from": _extract_sender_from_thread(d),
                "text": _extract_content_from_thread(d)[:2000],
            }
            for d in detailed
        ]

        # LLM extraction step
        import json

        def _validate_email_classification(data: Dict[str, Any]) -> Dict[str, Any]:
            out = {"interview_related_ids": [], "key_insights": [], "contacts": []}
            if isinstance(data, dict):
                if isinstance(data.get("interview_related_ids"), list):
                    out["interview_related_ids"] = [str(x) for x in data["interview_related_ids"] if x]
                if isinstance(data.get("key_insights"), list):
                    out["key_insights"] = [str(x) for x in data["key_insights"] if x]
                if isinstance(data.get("contacts"), list):
                    clean = []
                    for c in data["contacts"]:
                        if isinstance(c, dict) and c.get("email"):
                            clean.append({
                                "email": str(c.get("email")),
                                "name": str(c.get("name")) if c.get("name") else "",
                                "subject": str(c.get("subject")) if c.get("subject") else "",
                            })
                    out["contacts"] = clean
            return out

        content = "{}"
        try:
            import asyncio
            with self.logger.timed(step="act:llm_email_classify", tool="OpenAI.ChatCompletions") as t:
                completion = await asyncio.to_thread(
                    self.openai.chat.completions.create,
                    model=self.config.openai_model,
                    messages=[
                        {"role": "system", "content": "Return JSON only. No prose."},
                        {"role": "user", "content": (
                            "Given emails (id, subject, from, text), for domain " + company_domain + 
                            ", find interview-related ids, key insights, and contacts. "
                            "Respond strictly as JSON with keys: interview_related_ids, key_insights, contacts."
                        )},
                        {"role": "user", "content": json.dumps(compact) },
                    ],
                    temperature=0,
                    max_tokens=700,
                )
                t.result("ok")
                content = completion.choices[0].message.content or "{}"
        except Exception as e:
            # Logged in timer
            content = "{}"

        try:
            data = _validate_email_classification(json.loads(content))
        except Exception:
            data = _validate_email_classification({})

        id_set = set(data.get("interview_related_ids", []))
        interview_related: List[CompanyEmail] = []
        for d in detailed:
            if d.get("id") in id_set:
                interview_related.append(CompanyEmail(
                    id=d.get("id", ""),
                    subject=_extract_subject_from_thread(d),
                    sender=_extract_sender_from_thread(d),
                    date=str(d.get("internalDate") or ""),
                    content=_extract_content_from_thread(d),
                    thread_data=d,
                ))

        contacts_out: List[Dict[str, str]] = []
        for c in data.get("contacts", []) or []:
            if isinstance(c, dict) and c.get("email"):
                contacts_out.append({
                    "email": c.get("email"),
                    "name": c.get("name") or (c.get("email", "").split("@")[0].replace(".", " ").title()),
                    "subject": (c.get("subject") or "")[:120],
                })

        return EmailInsight(
            total_emails=len(detailed),
            interview_related=interview_related,
            key_insights=list({str(s) for s in (data.get("key_insights") or [])}),
            important_contacts=contacts_out[:10],
        )
