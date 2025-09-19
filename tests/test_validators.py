import os
from utils.validators import is_safe_domain, ensure_https, sanitize_url


def test_is_safe_domain_valid():
    assert is_safe_domain("example.com")
    assert is_safe_domain("sub.example.org")


def test_is_safe_domain_invalid():
    assert not is_safe_domain("javascript:alert(1)")
    assert not is_safe_domain("exa mple.com")


def test_ensure_https():
    assert ensure_https("example.com") == "https://example.com"
    assert ensure_https("http://example.com") == "https://example.com"
    assert ensure_https("https://example.com") == "https://example.com"


def test_sanitize_url():
    assert sanitize_url("example.com/about") == "https://example.com/about"
    assert sanitize_url("http://example.com/about") == "https://example.com/about"
    # Remove query/fragment and unsafe chars from path
    assert sanitize_url("https://example.com/ab<>out?q=1#frag").startswith("https://example.com/ab")

