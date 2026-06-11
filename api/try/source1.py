# """
# News Sources Fetcher V2
# Sources: Google News RSS + GDELT
# Scraping: Trafilatura (Full content)
# Storage: PostgreSQL
# """

# import os
# import time
# import hashlib
# import re
# from datetime import datetime, timezone
# from typing import Optional

# import feedparser
# import httpx
# import trafilatura
# from dotenv import load_dotenv

# from src.db import DBManager

# load_dotenv()

# # ─── CONFIG ───────────────────────────────────────────────

# GOOGLE_NEWS_FEEDS = [
#     {"name": "Google News — Top Stories", "url": "https://news.google.com/rss?hl=en&gl=US&ceid=US:en"},
#     {"name": "Google News — Technology", "url": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en&gl=US&ceid=US:en"},
#     {"name": "Google News — Business", "url": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en&gl=US&ceid=US:en"},
#     {"name": "Google News — Science", "url": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en&gl=US&ceid=US:en"},
#     {"name": "Google News — Health", "url": "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=en&gl=US&ceid=US:en"},
#     {"name": "Google News — Sports", "url": "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en&gl=US&ceid=US:en"},
#     {"name": "Google News — World", "url": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en&gl=US&ceid=US:en"},
# ]

# GDELT_URL = (
#     "https://api.gdeltproject.org/api/v2/doc/doc"
#     "?query=&mode=artlist&maxrecords=50"
#     "&sourcelang=english&format=json"
# )

# # ─── HELPERS ──────────────────────────────────────────────

# def make_id(url: str) -> str:
#     return hashlib.md5(url.encode()).hexdigest()[:12]

# def clean_title(title: str) -> str:
#     if not title: return ""
#     if " - " in title:
#         title = title.rsplit(" - ", 1)[0]
#     return title.strip()

# def scrape_article(url: str) -> dict:
#     """Use trafilatura to extract full content and metadata"""
#     try:
#         downloaded = trafilatura.fetch_url(url)
#         if not downloaded:
#             return {}
        
#         metadata = trafilatura.extract_metadata(downloaded)
#         content = trafilatura.extract(downloaded, include_comments=False)
        
#         return {
#             "content": content or "",
#             "author": metadata.author if metadata else None,
#             "image_url": metadata.image if metadata else None,
#             "date": metadata.date if metadata else None
#         }
#     except Exception as e:
#         print(f"      [Scrape Error] {url[:50]}... : {e}")
#         return {}

# # ─── FETCHERS ─────────────────────────────────────────────

# def fetch_rss_urls(feed_config: dict) -> list[dict]:
#     urls = []
#     try:
#         feed = feedparser.parse(feed_config["url"])
#         for entry in feed.entries[:15]:
#             url = getattr(entry, "link", "")
#             title = getattr(entry, "title", "")
#             if url:
#                 urls.append({"url": url, "title": title, "source": feed_config["name"]})
#     except Exception as e:
#         print(f"   ✗ Error fetching {feed_config['name']}: {e}")
#     return urls

# def fetch_gdelt_urls() -> list[dict]:
#     urls = []
#     try:
#         with httpx.Client(timeout=15) as client:
#             response = client.get(GDELT_URL)
#             data = response.json()
#         for item in data.get("articles", []):
#             url = item.get("url")
#             title = item.get("title")
#             if url:
#                 urls.append({"url": url, "title": title, "source": item.get("domain", "GDELT")})
#     except Exception as e:
#         print(f"   ✗ Error fetching GDELT: {e}")
#     return urls

# # ─── MAIN ─────────────────────────────────────────────────

# def run_pipeline():
#     db = DBManager()
#     print("\n🚀 Starting Article Fetcher Pipeline...")
    
#     # 1. Collect URLs
#     all_targets = []
#     print("\n📡 Collecting URLs from RSS...")
#     for feed in GOOGLE_NEWS_FEEDS:
#         all_targets.extend(fetch_rss_urls(feed))
#         print(f"   ✓ {feed['name']}")
    
#     # print("\n📡 Collecting URLs from GDELT...")
#     # all_targets.extend(fetch_gdelt_urls())

#     # 2. Deduplicate and filter (could also check DB here)
#     unique_targets = {t["url"]: t for t in all_targets}.values()
#     print(f"\n📦 Found {len(all_targets)} total URLs, {len(unique_targets)} unique.")

#     # 3. Scrape & Save
#     count = 0
#     print("\n📥 Scraping and saving to DB...")
#     for target in unique_targets:
#         url = target["url"]
#         article_id = make_id(url)
        
#         # Quick check if exists to save time/resources
#         # (Though DBManager.insert_article handles ON CONFLICT DO NOTHING, 
#         # we avoid scraping if it's already there)
        
#         print(f"   [{count+1}/{len(unique_targets)}] Processing: {url[:60]}...")
        
#         scraped = scrape_article(url)
#         if not scraped or not scraped.get("content"):
#             print("      ⚠️ No content extracted, skipping.")
#             continue

#         article_data = {
#             "id": article_id,
#             "url": url,
#             "title": clean_title(target["title"]),
#             "source_name": target["source"],
#             "image_url": scraped.get("image_url"),
#             "author": scraped.get("author"),
#             "published_at": scraped.get("date") or datetime.now(timezone.utc).isoformat(),
#             "content": scraped["content"],
#             "status": "pending"
#         }
        
#         try:
#             db.insert_article(article_data)
#             count += 1
#         except Exception as e:
#             print(f"      ❌ DB Error: {e}")

#     print(f"\n✅ Pipeline complete. {count} articles saved/updated in DB (pending status).")

# if __name__ == "__main__":
#     run_pipeline()


# if __name__ == "__main__":
#     main()