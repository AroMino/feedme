import os
import json
from groq import Groq
from dotenv import load_dotenv
from src.db import DBManager
from src.scorer import Scorer

load_dotenv()

class ArticleProcessor:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.db = DBManager()
        self.scorer = Scorer()

    def process_pending_articles(self, limit=5):
        articles = self.db.get_pending_articles(limit=limit)
        print(f"🧠 Processing {len(articles)} pending articles...")
        
        for art in articles:
            print(f"   → Analyzing: {art['title'][:60]}...")
            enrichment = self.analyze_content(art['content'])
            if enrichment:
                self.db.update_article_enrichment(art['id'], enrichment)
                print(f"      ✅ Enriched: {enrichment.get('topics', [])}")
                
                # NEW: Score for all users
                self.scorer.score_article_to_all_users(art['id'])
            else:
                print(f"      ❌ Enrichment failed for {art['id']}")

    def analyze_content(self, content: str) -> dict:
        """Analyze full content with Groq to get structured enrichments"""
        content_preview = content[:15000] 

        prompt = f"""
        Analyze the following article content and provide technical enrichment in English.
        Return ONLY a JSON object with the following fields:
        - topics: list of 3-5 broad and specific topics (e.g. ["Artificial Intelligence", "Nvidia", "Data Centers"])
        - summary: concise summary (2-3 sentences)
        - global_relevance: score from 0.0 to 1.0 (how important/impactful this news is globally)
        - content_quality: score from 0.0 to 1.0 (writing quality, depth, and reliability)
        - popularity_score: score from 0.0 to 1.0 (how much this news is trending/popular right now)

        Article content:
        {content_preview}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a news analyst expert. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"      [LLM Error] {e}")
            return None

if __name__ == "__main__":
    processor = ArticleProcessor()
    processor.process_pending_articles(limit=10)
