import hashlib

from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    """Strip query parameters and fragments from a URL for consistent identification"""
    if not url: return ""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

def make_id(url: str) -> str:
    """Generate a stable 12-char ID from a normalized URL"""
    normalized = normalize_url(url)
    return hashlib.md5(normalized.encode()).hexdigest()[:12]

def clean_title(title: str) -> str:
    """Remove source suffixes from titles (e.g. ' - BBC News')"""
    if not title: return ""
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
    return title.strip()
