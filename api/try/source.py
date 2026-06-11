"""
News Sources Fetcher
Fetches articles from RSS feeds and NewsAPI
Deduplicates and stores results
"""

import os
import time
import hashlib
import asyncio
import json
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional

import feedparser
import httpx
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")  # optional

# ─── DATA MODEL ───────────────────────────────────────────

@dataclass
class RawArticle:
    id:           str        # hash of url
    title:        str
    content:      str
    url:          str
    source_name:  str
    source_url:   str
    image_url:    Optional[str]
    author:       Optional[str]
    published_at: str
    fetched_at:   str
    language:     str = "en"
    status:       str = "pending"  # pending → processed


# ─── RSS SOURCES ──────────────────────────────────────────

RSS_SOURCES = [
    # Source principale — top stories
    {
        "name": "Google News",
        "url": "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
    },
    # Source secondaire — volume + niches
    {
        "name": "GDELT",
        "url": "https://api.gdeltproject.org/api/v2/doc/doc?query=&mode=artlist&maxrecords=100&format=json",
    },
]

# ─── HELPERS ──────────────────────────────────────────────

def make_id(url: str) -> str:
    """Generate unique ID from URL"""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def clean_text(text: str) -> str:
    """Remove HTML tags and extra whitespace"""
    import re
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_date(entry) -> str:
    """Extract and normalize publication date"""
    for field in ["published_parsed", "updated_parsed"]:
        val = getattr(entry, field, None)
        if val:
            try:
                dt = datetime(*val[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def extract_image(entry) -> Optional[str]:
    """Try to extract image URL from RSS entry"""
    # Method 1 — media:thumbnail
    media = getattr(entry, "media_thumbnail", None)
    if media and len(media) > 0:
        return media[0].get("url")

    # Method 2 — media:content
    media = getattr(entry, "media_content", None)
    if media and len(media) > 0:
        url = media[0].get("url", "")
        if any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            return url

    # Method 3 — enclosures
    enclosures = getattr(entry, "enclosures", [])
    for enc in enclosures:
        if "image" in enc.get("type", ""):
            return enc.get("href")

    return None


# ─── RSS FETCHER ──────────────────────────────────────────

def fetch_rss_source(source: dict) -> list[RawArticle]:
    """Fetch and parse a single RSS feed"""
    articles = []
    now = datetime.now(timezone.utc).isoformat()

    try:
        feed = feedparser.parse(source["url"])

        if feed.bozo and not feed.entries:
            print(f"   ⚠️  {source['name']}: feed error — {feed.bozo_exception}")
            return []

        for entry in feed.entries[:15]:  # max 15 per source
            url = getattr(entry, "link", "")
            if not url:
                continue

            # Extract content
            content = ""
            if hasattr(entry, "content") and entry.content:
                content = clean_text(entry.content[0].get("value", ""))
            elif hasattr(entry, "summary"):
                content = clean_text(entry.summary)
            elif hasattr(entry, "description"):
                content = clean_text(entry.description)

            title = clean_text(getattr(entry, "title", ""))
            if not title or len(title) < 5:
                continue

            article = RawArticle(
                id           = make_id(url),
                title        = title,
                content      = content[:2000],   # limit to 2000 chars
                url          = url,
                source_name  = source["name"],
                source_url   = source["url"],
                image_url    = extract_image(entry),
                author       = getattr(entry, "author", None),
                published_at = parse_date(entry),
                fetched_at   = now,
            )
            articles.append(article)

        print(f"   ✓  {source['name']:<20} {len(articles)} articles")

    except Exception as e:
        print(f"   ✗  {source['name']:<20} Error: {e}")

    return articles


def fetch_all_rss() -> list[RawArticle]:
    """Fetch all RSS sources sequentially"""
    all_articles = []
    print(f"\n📡 Fetching {len(RSS_SOURCES)} RSS sources...\n")

    for source in RSS_SOURCES:
        articles = fetch_rss_source(source)
        all_articles.extend(articles)
        time.sleep(0.3)  # polite delay

    return all_articles


# ─── NEWSAPI FETCHER (optional) ───────────────────────────

def fetch_newsapi(query: str = "technology AI", page_size: int = 20) -> list[RawArticle]:
    """Fetch from NewsAPI (requires free API key)"""
    if not NEWSAPI_KEY:
        print("   ⚠️  NEWSAPI_KEY not set, skipping NewsAPI")
        return []

    articles = []
    now = datetime.now(timezone.utc).isoformat()

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey":   NEWSAPI_KEY,
            "language": "en",
            "pageSize": page_size,
            "country": "fr",
            # "category": "technology"
        }

        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params)
            data = response.json()

        if data.get("status") != "ok":
            print(f"   ✗  NewsAPI error: {data.get('message')}")
            return []

        for item in data.get("articles", []):
            art_url = item.get("url", "")
            if not art_url or "[Removed]" in art_url:
                continue

            content = clean_text(item.get("content") or item.get("description") or "")

            article = RawArticle(
                id           = make_id(art_url),
                title        = clean_text(item.get("title", "")),
                content      = content[:2000],
                url          = art_url,
                source_name  = item.get("source", {}).get("name", "NewsAPI"),
                source_url   = "",
                image_url    = item.get("urlToImage"),
                author       = item.get("author"),
                published_at = item.get("publishedAt", now),
                fetched_at   = now,
            )
            articles.append(article)

        print(f"   ✓  NewsAPI: {len(articles)} articles")

    except Exception as e:
        print(f"   ✗  NewsAPI error: {e}")

    return articles


# ─── DEDUPLICATION ────────────────────────────────────────

def deduplicate(articles: list[RawArticle]) -> list[RawArticle]:
    """Remove duplicate articles by ID (URL hash)"""
    seen = set()
    unique = []
    for article in articles:
        if article.id not in seen:
            seen.add(article.id)
            unique.append(article)
    return unique


# ─── MAIN ─────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  NEWS SOURCES FETCHER")
    print("=" * 60)

    start = time.time()

    # 1 — Fetch RSS
    rss_articles = fetch_all_rss()

    # 2 — Fetch NewsAPI (optional)
    print(f"\n📡 Fetching NewsAPI...")
    api_articles = fetch_newsapi()

    # 3 — Merge & deduplicate
    all_articles = deduplicate(rss_articles + api_articles)

    elapsed = round(time.time() - start, 2)

    # 4 — Stats
    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  RSS articles       : {len(rss_articles)}")
    print(f"  NewsAPI articles   : {len(api_articles)}")
    print(f"  After deduplication: {len(all_articles)}")
    print(f"  Time elapsed       : {elapsed}s")

    # 5 — Save to JSON (later → PostgreSQL)
    output_file = "fetched_articles.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [asdict(a) for a in all_articles],
            f, indent=2, ensure_ascii=False
        )
    print(f"\n💾 Saved to {output_file}")

    # 6 — Preview first 5
    print(f"\n📰 Preview (first 5 articles):\n")
    for a in all_articles:
        print(f"   [{a.source_name}] {a.title[:60]}")
        print(f"   {a.url}")
        print(f"   Published: {a.published_at[:10]}  |  Content: {len(a.content)} chars\n")

    return all_articles


if __name__ == "__main__":
    main()