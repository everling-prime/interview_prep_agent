"""
Baseline example: realistic additional code required WITHOUT Arcade.dev.

This standalone file demonstrates the kinds of boilerplate typically needed to:
- Authenticate with Google (OAuth2) and persist/refresh tokens
- Initialize Gmail and Google Docs API clients
- List and fetch emails by company domain with pagination
- Create and populate a Google Doc with retry/backoff

It does not integrate with the rest of this repo. It’s illustrative only.
To actually run it, you would need to install the Google API libraries and
provide valid OAuth credentials and scopes.

Arcade.dev abstracts most of this: auth, token storage, client plumbing,
pagination, and robust retries for common operations.
"""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

# Third‑party: only needed if you actually run this baseline
# pip install google-auth google-auth-oauthlib google-api-python-client
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except Exception:  # pragma: no cover - illustrative import guard
    Credentials = object  # type: ignore
    Request = object  # type: ignore
    InstalledAppFlow = object  # type: ignore
    build = lambda *args, **kwargs: None  # type: ignore
    class HttpError(Exception):  # type: ignore
        status_code = None


@dataclass
class BaselineConfig:
    """Configuration strictly for this baseline example."""

    # OAuth client secret JSON downloaded from Google Cloud Console
    google_oauth_client_secret_file: str = "./credentials/client_secret.json"

    # Token cache for user credentials (created on first run)
    google_user_token_file: str = "./credentials/token.json"

    # Scopes needed for Gmail read and Docs write
    google_scopes: List[str] = (
        [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/documents",
        ]
    )

    # Optional: impersonated user/email; for installed apps use "me"
    gmail_user_id: str = "me"


def get_google_credentials(
    *, client_secret_file: str, token_file: str, scopes: Iterable[str]
) -> Credentials:
    """Obtain cached or fresh OAuth2 user credentials with refresh support."""

    creds: Optional[Credentials] = None  # type: ignore[assignment]
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)  # type: ignore[attr-defined]

    if not creds or not getattr(creds, "valid", False):
        if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            creds.refresh(Request())  # type: ignore[misc]
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)  # type: ignore[misc]
            creds = flow.run_local_server(port=0)  # type: ignore[misc]

        # Persist to token cache for future runs
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "w") as f:
            f.write(creds.to_json())  # type: ignore[union-attr]

    return creds  # type: ignore[return-value]


def build_gmail_service(creds: Credentials):
    """Initialize Gmail API client."""
    return build("gmail", "v1", credentials=creds)  # type: ignore[misc]


def build_docs_service(creds: Credentials):
    """Initialize Google Docs API client."""
    return build("docs", "v1", credentials=creds)  # type: ignore[misc]


def execute_with_backoff(request, *, max_retries: int = 5, base_delay: float = 0.5):
    """Execute a Google API request with exponential backoff for rate limits."""
    attempt = 0
    while True:
        try:
            return request.execute()
        except HttpError as e:  # type: ignore[misc]
            status = getattr(e, "status_code", None) or getattr(e, "resp", {}).get("status")
            if status in {403, 429, 500, 503} and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                attempt += 1
                continue
            raise


def list_messages_for_domain(
    gmail_service,
    *,
    user_id: str,
    domain: str,
    max_messages: int = 200,
) -> List[str]:
    """List message IDs for emails received from a given company domain."""

    query = f"from:*@{domain}"
    msg_ids: List[str] = []
    page_token: Optional[str] = None

    while True:
        request = (
            gmail_service.users()
            .messages()
            .list(userId=user_id, q=query, maxResults=100, pageToken=page_token)
        )
        resp = execute_with_backoff(request) or {}
        for item in resp.get("messages", []):
            msg_ids.append(item.get("id"))
            if len(msg_ids) >= max_messages:
                return msg_ids
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return msg_ids


def fetch_message_snippet(gmail_service, *, user_id: str, msg_id: str) -> str:
    """Fetch a message and return a decoded text snippet or subject line."""

    request = gmail_service.users().messages().get(userId=user_id, id=msg_id, format="full")
    resp = execute_with_backoff(request) or {}

    # Prefer the snippet, fall back to a decoded text/plain part if present
    snippet = resp.get("snippet")
    if snippet:
        return snippet

    payload = resp.get("payload", {})
    mime = payload.get("mimeType")
    if mime == "text/plain" and payload.get("body", {}).get("data"):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data.encode()).decode(errors="ignore")

    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data.encode()).decode(errors="ignore")

    headers = {h.get("name"): h.get("value") for h in (payload.get("headers") or [])}
    return headers.get("Subject", "")


def baseline_fetch_company_emails(
    *,
    domain: str,
    config: Optional[BaselineConfig] = None,
) -> List[str]:
    """End-to-end: auth + Gmail list + fetch snippets (baseline path)."""

    cfg = config or BaselineConfig()
    creds = get_google_credentials(
        client_secret_file=cfg.google_oauth_client_secret_file,
        token_file=cfg.google_user_token_file,
        scopes=cfg.google_scopes,
    )
    gmail = build_gmail_service(creds)
    msg_ids = list_messages_for_domain(gmail, user_id=cfg.gmail_user_id, domain=domain)
    snippets: List[str] = []
    for msg_id in msg_ids:
        try:
            snippets.append(fetch_message_snippet(gmail, user_id=cfg.gmail_user_id, msg_id=msg_id))
        except Exception:
            # Swallow per-message failures to keep the example minimal
            continue
    return snippets


def baseline_create_google_doc(
    *, title: str, paragraphs: List[str], config: Optional[BaselineConfig] = None
) -> str:
    """Create a Google Doc and insert content with basic chunking + retry."""

    cfg = config or BaselineConfig()
    creds = get_google_credentials(
        client_secret_file=cfg.google_oauth_client_secret_file,
        token_file=cfg.google_user_token_file,
        scopes=cfg.google_scopes,
    )
    docs = build_docs_service(creds)

    # Create doc
    create_request = docs.documents().create(body={"title": title})
    created = execute_with_backoff(create_request) or {}
    document_id = created.get("documentId")
    if not document_id:
        raise RuntimeError("Failed to create Google Doc")

    # Build batchUpdate requests to insert paragraphs
    requests: List[Dict] = []
    for p in paragraphs:
        requests.append(
            {
                "insertText": {
                    "text": p + "\n\n",
                    "location": {"index": 1},  # insert at beginning repeatedly
                }
            }
        )

    # Send in chunks to avoid large payloads
    chunk_size = 100
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i : i + chunk_size]
        update_req = docs.documents().batchUpdate(
            documentId=document_id, body={"requests": list(reversed(chunk))}
        )
        execute_with_backoff(update_req)

    return document_id


def demo_baseline_without_arcade(domain: str = "example.com") -> None:
    """Illustrative demo that exercises both email and docs operations."""

    # Emails
    snippets = baseline_fetch_company_emails(domain=domain)

    # Minimal doc content: first 10 snippets
    top = [f"- {s}" for s in snippets[:10]] or ["- No snippets found"]
    doc_id = baseline_create_google_doc(
        title=f"Interview Prep — {domain}", paragraphs=["Email snippets:", *top]
    )

    print(f"Created Google Doc: https://docs.google.com/document/d/{doc_id}/edit")


if __name__ == "__main__":
    print(
        "This file is an illustrative baseline. To run it, install Google API\n"
        "libraries and configure OAuth client + token paths in BaselineConfig,\n"
        "then call demo_baseline_without_arcade('<company-domain>')."
    )

