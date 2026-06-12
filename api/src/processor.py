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
        print(f"Processing {len(articles)} pending articles...")
        
        for art in articles:
            print(f"   -> Analyzing: {art['title'][:60]}...")
            enrichment = self.analyze_content(art['content'])
            if enrichment:
                self.db.update_article_enrichment(art['id'], enrichment)
                print(f"      [OK] Enriched: {enrichment.get('topics', [])}")
            else:
                print(f"      [Error] Enrichment failed for {art['id']}")

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

