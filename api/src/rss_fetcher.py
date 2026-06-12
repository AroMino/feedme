import time
from datetime import datetime, timezone
import feedparser
from src.db import DBManager
from src.utils.scraper import scrape_article_content
from src.utils.llm import LLMService
from src.utils.text import make_id, clean_title, normalize_url
import json

# ─── CONFIG ───────────────────────────────────────────────
LIMIT_PER_SOURCE = 20

RSS_SOURCES = [
    {"name": "BBC News - World",      "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "NYT - Home Page",       "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"},
    {"name": "Reuters - World News",  "url": "https://www.reutersagency.com/feed/?best-types=world-news&post_type=best"},
    # {"name": "The Guardian - World",  "url": "https://www.theguardian.com/world/rss"},
]

class RSSFetcher:
    def __init__(self):
        self.db = DBManager()
        self.llm = LLMService()

    def run(self):
        print("\nStarting AI-Powered RSS Fetcher...")
        
        total_new = 0
        for source in RSS_SOURCES:
            print(f"\nParsing Feed: {source['name']}...")
            try:
                feed = feedparser.parse(source["url"])
                print(f"   Found {len(feed.entries)} entries.")
                
                source_count = 0
                for entry in feed.entries:
                    if source_count >= LIMIT_PER_SOURCE:
                        print(f"   [Limit] Reached {LIMIT_PER_SOURCE} articles for {source['name']}. Moving next.")
                        break
                        
                    # 1. Preliminary URL for deduplication
                    raw_url = entry.get("link")
                    if not raw_url: continue
                    
                    # NORMALIZE BEFORE CHECKING
                    url = normalize_url(raw_url)
                    
                    article_id = make_id(url)
                    if self.db.article_exists(article_id):
                        continue

                    print(f"   [New] Extracting with AI: {url[:60]}...")
                    
                    # 2. Use LLM to standardize varied RSS structures
                    entry_simple = {k: str(v) for k, v in entry.items() if k not in ['summary_detail', 'title_detail', 'content']}
                    
                    system_prompt = "You are a specialized RSS parser. Extract article metadata into a clean JSON format."
                    user_prompt = f"""
                    Review this RSS entry and extract the following fields in a JSON object:
                    - url: The main article link.
                    - title: The article title.
                    - author: The author name or news source name.
                    - published_at: The publication date in ISO 8601 format (UTC).
                    - image_url: The URL of the main article image (check media:content, enclosures, etc).

                    RSS Entry Data:
                    {json.dumps(entry_simple, indent=2)[:4000]}
                    """
                    
                    standard_data = self.llm.get_json(system_prompt, user_prompt)
                    if not standard_data:
                        print("      [Error] AI Parsing failed.")
                        continue

                    target_url = normalize_url(standard_data.get("url") or url)
                    
                    # 3. Scrape full content
                    full_content = scrape_article_content(target_url)
                    
                    # Fallback to RSS summary
                    summary_fallback = entry.get("summary") or entry.get("description") or ""
                    content = full_content if (full_content and len(full_content) > 200) else summary_fallback

                    if len(content) < 100:
                        print("      [Skip] Content too short.")
                        continue

                    article_data = {
                        "id": make_id(target_url),
                        "url": target_url,
                        "title": clean_title(standard_data.get("title") or entry.get("title")),
                        "image_url": standard_data.get("image_url") or entry.get("media_content", [{}])[0].get("url"),
                        "author": standard_data.get("author") or entry.get("author") or source["name"],
                        "published_at": standard_data.get("published_at") or datetime.now(timezone.utc).isoformat(),
                        "content": content,
                        "status": "pending"
                    }

                    try:
                        self.db.insert_article(article_data)
                        total_new += 1
                        source_count += 1
                        # Respectful pulsing between scrapes
                        time.sleep(1)
                    except Exception as e:
                        print(f"      [DB Error] {e}")

            except Exception as e:
                print(f"   [Error] processing feed {source['name']}: {e}")

        print(f"\nRSS Fetcher complete. {total_new} new articles saved to DB.")

if __name__ == "__main__":
    RSSFetcher().run()
