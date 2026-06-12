from src.utils.llm import LLMService
from src.db import DBManager
from src.scorer import Scorer

class ArticleProcessor:
    def __init__(self):
        self.llm = LLMService()
        self.db = DBManager()
        self.scorer = Scorer()

    def process_pending_articles(self, limit=5):
        articles = self.db.get_pending_articles(limit=limit)
        if not articles:
            return
            
        print(f"Processing {len(articles)} pending articles...")
        
        all_new_topics = set()
        for art in articles:
            print(f"   -> Analyzing: {art['title'][:60]}...")
            enrichment = self.analyze_content(art['content'])
            if enrichment:
                self.db.update_article_enrichment(art['id'], enrichment)
                # Collect topics to ensure we have embeddings for them
                topics = enrichment.get('topics', []) + enrichment.get('global_topics', [])
                all_new_topics.update(topics)
                print(f"      [OK] Enriched: {enrichment.get('topics', [])}")
            else:
                print(f"      [Error] Enrichment failed for {art['id']}")

        # Bulk fetch embeddings for all topics that don't have them yet
        if all_new_topics:
            self._ensure_topic_embeddings(list(all_new_topics))

    def _ensure_topic_embeddings(self, topic_names):
        """Fetch and save embeddings for topics that are missing them"""
        missing_topics = []
        for name in topic_names:
            # We need the ID to save the embedding
            topic_id = self.db.get_or_create_topic(name)
            # Check if it already has an embedding
            # Note: get_or_create_topic doesn't return the embedding, 
            # so we might need a small helper or just attempt to fetch if we aren't sure.
            # For simplicity, we'll use a direct query here or add a method to DB.
            with self.db.conn.cursor() as cur:
                cur.execute("SELECT 1 FROM topics WHERE id = %s AND embedding IS NOT NULL", (topic_id,))
                if not cur.fetchone():
                    missing_topics.append((topic_id, name))
        
        if missing_topics:
            print(f"🏷️  Found {len(missing_topics)} new topics needing embeddings. Batching...")
            t_ids = [t[0] for t in missing_topics]
            t_names = [t[1] for t in missing_topics]
            
            # Batch of 50 to avoid rate limits
            for i in range(0, len(t_names), 50):
                batch_names = t_names[i:i+50]
                batch_ids = t_ids[i:i+50]
                try:
                    embs = self.scorer.get_embeddings_batch(batch_names)
                    for tid, emb in zip(batch_ids, embs):
                        if emb:
                            self.db.save_topic_embedding(tid, emb)
                except Exception as e:
                    print(f"      [Warning] Failed to fetch embeddings for batch: {e}")

    def analyze_deep(self, content: str) -> dict:
        """Deep analysis focused on context, detailed analysis and commentary"""
        content_preview = content[:18000] 

        system_prompt = "You are a senior technology and news analyst."
        user_prompt = f"""
        Provide a deep expert analysis of the following article in English.
        Return ONLY a JSON object with the following fields:
        - ai_explanation: String. Broad context and background explanation of why this matter right now.
        - ai_analysis: String (Markdown). Detailed technical or strategic analysis of the news. Do NOT use nested objects.
        - ai_commentary: String (Markdown). Critical commentary or future outlook. Do NOT use nested objects.

        Article content:
        {content_preview}
        """
        return self.llm.get_json(system_prompt, user_prompt)

    def analyze_content(self, content: str) -> dict:
        """Analyze full content with Groq to get structured enrichments"""
        content_preview = content[:15000] 

        system_prompt = "You are a news analyst expert. Return ONLY valid JSON. Ensure long strings are correctly quoted and escaped."
        user_prompt = f"""
        Analyze the following article content and provide highly engaging enrichment in English.
        
        Return ONLY a JSON object with the following fields:
        - topics: list of 3-5 specific topics (e.g. ["M4 Chip", "OLED Display", "iPad Pro"])
        - global_topics: list of 2-3 broad, high-level categories for interest following (e.g. ["Technology", "Computing", "Apple"])
        - summary: A complete and compelling summary (3-5 sentences). Synthesize the most critical information into an attractive narrative.
        - global_relevance: Float (0.0 to 1.0). BE HONEST. 
            Rubric: 
            - 0.1-0.3: Local/Niche news (minimal impact). 
            - 0.4-0.6: Regional/Industry news (significant interest group). 
            - 0.7-0.9: Major Global news ( breakthrough tech, events affecting millions). 
            - 1.0: Paradigm-shifting global events.
        - content_quality: Float (0.0 to 1.0). BE CRITICAL. 
            Rubric: 
            - 0.1-0.3: Thin content, clickbait, or poor formatting. 
            - 0.4-0.6: Factual reporting but basic/derivative. 
            - 0.7-0.9: Investigative, expert analysis, or high-depth storytelling. 
            - 1.0: Definitive resource/Exceptional work.
        - popularity_score: score from 0.0 to 1.0

        Article content:
        {content_preview}
        """
        return self.llm.get_json(system_prompt, user_prompt)

if __name__ == "__main__":
    processor = ArticleProcessor()
    processor.process_pending_articles(limit=10)

