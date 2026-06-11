import sys
import os

# Add src to path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.fetcher import Fetcher
from src.processor import ArticleProcessor
from src.scorer import Scorer
from src.db import DBManager

def main():
    # Initialize DB (creates/normalizes tables using schema.sql)
    db = DBManager()
    db.init_db()

    # 1. Fetch & Scrape
    print("\n--- STEP 1: FETCHING ---")
    fetcher = Fetcher()
    fetcher.run()

    # 2. Process / Enrich with LLM
    print("\n--- STEP 2: PROCESSING ---")
    processor = ArticleProcessor()
    processor.process_pending_articles(limit=10)

    # 3. Score for all users
    print("\n--- STEP 3: SCORING ---")
    scorer = Scorer()
    users = db.get_users()
    
    for user in users:
        print(f"👤 Processing feed for: {user['name']} ({user['email']})")
        scorer.score_all_for_user(user['id'])

    print("\n✨ Pipeline execution finished.")

if __name__ == "__main__":
    main()
