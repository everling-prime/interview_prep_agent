import re
from urllib.parse import urlparse, urlunparse


_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def is_safe_domain(domain: str) -> bool:
    domain = (domain or "").strip().lower()
    if domain.startswith("http://") or domain.startswith("https://"):
        try:
            parsed = urlparse(domain)
            domain = parsed.netloc
        except Exception:
            return False
    return bool(_DOMAIN_RE.match(domain)) and not any(ch in domain for ch in [' ', '\\', '"', "'"])


def ensure_https(url_or_domain: str) -> str:
    s = (url_or_domain or "").strip()
    if not s:
        return s
    if s.startswith("http://"):
        s = "https://" + s[len("http://"):]
    elif not s.startswith("https://"):
        # looks like a bare domain
        s = f"https://{s}"
    return s


def sanitize_url(url_or_domain: str) -> str:
    s = ensure_https(url_or_domain)
    try:
        p = urlparse(s)
        # Only keep scheme + netloc + safe path
        safe_path = re.sub(r"[^a-zA-Z0-9_./-]", "", p.path or "/")
        safe = urlunparse(("https", p.netloc.lower(), safe_path, "", "", ""))
        return safe
    except Exception:
        return s

