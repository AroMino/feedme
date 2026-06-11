import os
import time
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from dotenv import load_dotenv

from src.db import DBManager

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────

NEWSAPI_TOP_URL = "https://newsapi.org/v2/top-headlines"
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# ─── HELPERS ──────────────────────────────────────────────

def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]

def clean_title(title: str) -> str:
    if not title: return ""
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
    return title.strip()

# ─── FETCHERS ─────────────────────────────────────────────

def fetch_top_headlines(limit=50) -> list[dict]:
    """Fetch top headlines from NewsAPI for US"""
    articles = []
    if not NEWSAPI_KEY:
        print("   ❌ NEWSAPI_KEY not found in .env")
        return []

    try:
        params = {
            # "country": "us",
            "apiKey": NEWSAPI_KEY,
            "pageSize": limit
        }
        with httpx.Client(timeout=15) as client:
            response = client.get(NEWSAPI_TOP_URL, params=params)
            data = response.json()
            
            if data.get("status") == "error":
                print(f"   ✗ NewsAPI Error: {data.get('message')}")
                return []

            for item in data.get("articles", []):
                # Skip articles with removed content
                if "[Removed]" in item.get("title", "") or not item.get("url"):
                    continue
                
                # We prioritize 'content', but 'description' is a good backup
                content = item.get("content") or item.get("description") or ""
                
                articles.append({
                    "url": item["url"],
                    "title": item["title"],
                    "author": item.get("author"),
                    "published": item.get("publishedAt"),
                    "image": item.get("urlToImage"),
                    "description": item.get("description"),
                    "source": item.get("source", {}).get("name", "NewsAPI"),
                    "content": content
                })
    except Exception as e:
        print(f"   ✗ Error calling NewsAPI Top Headlines: {e}")
    return articles

class Fetcher:
    def __init__(self):
        self.db = DBManager()

    def run(self):
        print("\n🚀 Starting NewsAPI Fetcher Pipeline (Top Headlines US)...")
        
        # 1. Collect URLs from NewsAPI Top Headlines
        print(f"\n📡 Fetching Top Headlines (US)...")
        results = fetch_top_headlines(limit=100)
        
        # 2. Deduplicate
        unique_targets = {t["url"]: t for t in results}.values()
        print(f"\n📦 Found {len(results)} total articles, {len(unique_targets)} unique.")

        # 3. Save to DB
        count = 0
        print("\n📥 Saving to DB...")
        for target in unique_targets:
            url = target["url"]
            article_id = make_id(url)
            
            print(f"   [{count+1}/{len(unique_targets)}] Processing: {url[:60]}...")
            
            content = target.get("content") or ""
            
            if len(content) < 100: # Reduced threshold as NewsAPI content is often short
                print("      ⚠️ Content too short, skipping.")
                continue

            article_data = {
                "id": article_id,
                "url": url,
                "title": clean_title(target["title"]),
                "image_url": target.get("image"),
                "author": target.get("author"),
                "published_at": target.get("published") or datetime.now(timezone.utc).isoformat(),
                "content": content,
                "status": "pending"
            }
            
            try:
                self.db.insert_article(article_data)
                count += 1
            except Exception as e:
                print(f"      ❌ DB Error: {e}")

        print(f"\n✅ Fetcher complete. {count} articles saved/updated in DB.")

if __name__ == "__main__":
    Fetcher().run()
