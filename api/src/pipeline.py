import sys
import os

from src.rss_fetcher import RSSFetcher
from src.processor import ArticleProcessor

def run():
    """Main ingestion and processing pipeline"""
    print("Starting Automated News Pipeline...")
    
    try:
        processor = ArticleProcessor()
        
        # 1. Process backlog first (clears ALL old pending articles)
        print("\n--- STEP 1: CLEARING ENTIRE BACKLOG ---")
        while True:
            pending_check = processor.db.get_pending_articles(limit=1)
            if not pending_check:
                print("   [Done] Backlog is empty.")
                break
            processor.process_pending_articles(limit=30)
        
        # 2. Fetch from RSS
        print("\n--- STEP 2: RSS FETCHING ---")
        fetcher = RSSFetcher()
        fetcher.run()
        
        # 3. Process new articles (make them appear in feeds)
        print("\n--- STEP 3: PROCESSING NEW ARTICLES ---")
        processor.process_pending_articles(limit=50)
        
        print("\nPipeline finished successfully.")
    except Exception as e:
        print(f"\n[Error] Pipeline failed: {e}")
        # Let callers (like the scheduler) decide how to handle the failure
        raise e

if __name__ == "__main__":
    run()
