# import sys
# import os

# from src.rss_fetcher import RSSFetcher
# from src.processor import ArticleProcessor

# def run_rss_pipeline():
#     print("Starting RSS Automated Pipeline...")
    
#     try:
#         # 1. Fetch from RSS
#         print("\n--- STEP 1: RSS FETCHING ---")
#         fetcher = RSSFetcher()
#         fetcher.run()
        
#         # 2. Process & Enrich (AI summaries, topics, etc.)
#         print("\n--- STEP 2: PROCESSING & SCORING ---")
#         processor = ArticleProcessor()
#         processor.process_pending_articles(limit=50)
        
#         print("\nPipeline finished successfully.")
#     except Exception as e:
#         print(f"\n[Error] RSS Pipeline failed: {e}")
#         sys.exit(1)

# if __name__ == "__main__":
#     run_rss_pipeline()
