import os
import requests
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import trafilatura

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def fetch_with_retry(url: str) -> str:
    """Fetch URL content with realistic headers and retries"""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text

def scrape_article_content(url: str) -> Optional[str]:
    """Download and extract main content from URL using trafilatura"""
    try:
        # Use our robust fetcher first
        html_content = fetch_with_retry(url)
        if not html_content:
            return None
        
        # Extract from the HTML we downloaded
        result = trafilatura.extract(html_content, include_comments=False, include_tables=True)
        return result
    except Exception as e:
        print(f"      [Scrape Error] {url[:50]}: {e}")
        return None
