import os
import time
import numpy as np
from google import genai
from groq import Groq
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from src.db import DBManager

load_dotenv()

class Scorer:
    def __init__(self):
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.MODEL_EMBED = "gemini-embedding-001"
        self.GROQ_MAIN = "llama-3.3-70b-versatile"
        self.GROQ_FAST = "llama-3.1-8b-instant"
        self.db = DBManager()

    def get_embedding(self, text: str) -> list:
        """Get embedding from Gemini and return as list"""
        time.sleep(0.3) # Rate limit
        result = self.gemini_client.models.embed_content(
            model=self.MODEL_EMBED,
            contents=text
        )
        return result.embeddings[0].values

    # def enrich_user_interests(self, user_id, interests: list):
    #     """Expand user interests and detect topics"""
    #     print(f"👤 Enriching interests for user {user_id}...")
        
    #     # 1. Expand interests
    #     enriched_texts = []
    #     for interest in interests:
    #         enriched = self.expand_interest_llm(interest)
    #         enriched_texts.append(enriched)
        
    #     full_enriched = ", ".join(enriched_texts)
        
    #     # 2. Detect topic categories
    #     topics = self.detect_topics_llm(interests)
        
        # 3. Generate embeddings for enriched interests
    def get_embedding_with_cache(self, text, type="topic", id=None, name=None, user_id=None):
        """Get embedding and save to DB if id/name provided"""
        emb = self.get_embedding(text)
        if type == "topic" and id:
            self.db.save_topic_embedding(id, emb)
        elif type == "interest" and user_id and name:
            self.db.save_interest_embedding(user_id, name, emb)
        return emb

    def cosine_similarity(self, v1, v2):
        v1 = np.array(v1)
        v2 = np.array(v2)
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        return float(np.dot(v1, v2) / norm) if norm else 0.0

    def score_all_for_user(self, user_id):
        """Score articles for a specific user using topic-based matching"""
        # 1. Get user interests and their embeddings
        interests = self.db.get_user_interests(user_id)
        interest_embs = []
        for interest in interests:
            if not interest['embedding']:
                emb = self.get_embedding_with_cache(interest['interest_name'], type="interest", user_id=user_id, name=interest['interest_name'])
            else:
                emb = interest['embedding']
            interest_embs.append(emb)

        # 2. Get processed articles
        query = "SELECT * FROM articles WHERE status = 'processed'"
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            articles = cur.fetchall()

        print(f"⚖️  Scoring {len(articles)} articles for user {user_id}...")
        for art in articles:
            self._score_single(user_id, art, interest_embs)
        
        print(f"✅ Scoring complete for user {user_id}.")

    def score_article_to_all_users(self, article_id):
        """Score a single article for everyone in the system"""
        art = self.db.get_article_by_id(article_id)
        if not art or art['status'] != 'processed':
            return

        users = self.db.get_users()
        print(f"⚖️  Scoring article {article_id} for {len(users)} users...")
        
        for u in users:
            # Get user interests
            interests = self.db.get_user_interests(u['id'])
            interest_embs = []
            for interest in interests:
                if not interest['embedding']:
                    emb = self.get_embedding_with_cache(interest['interest_name'], type="interest", user_id=u['id'], name=interest['interest_name'])
                else:
                    emb = interest['embedding']
                interest_embs.append(emb)
            
            self._score_single(u['id'], art, interest_embs)

    def _score_single(self, user_id, art, interest_embs):
        """Helper to score one article for one user"""
        # 1. Get article topics and their embeddings
        topics = self.db.get_article_topics(art['id'])
        topic_embs = []
        for t in topics:
            if not t['embedding']:
                emb = self.get_embedding_with_cache(t['name'], type="topic", id=t['id'])
            else:
                emb = t['embedding']
            topic_embs.append(emb)

        # 2. Calculate Max Similarity
        max_sim = 0
        if interest_embs and topic_embs:
            for i_emb in interest_embs:
                for t_emb in topic_embs:
                    sim = self.cosine_similarity(i_emb, t_emb)
                    if sim > max_sim:
                        max_sim = sim

        # 3. Calculate Weights
        relevance = art['global_relevance'] or 0.5
        quality = art['content_quality'] or 0.5
        popularity = art['popularity_score'] or 0.5

        # weights for "For You"
        for_you = (max_sim * 0.6) + (relevance * 0.2) + (quality * 0.2)
        
        # weights for "Trending"
        trending = (popularity * 0.6) + (relevance * 0.2) + (quality * 0.2)

        score_data = {
            "user_id": user_id,
            "article_id": art['id'],
            "for_you_score": round(for_you, 3),
            "trending_score": round(trending, 3),
            "semantic_max_sim": round(max_sim, 3)
        }
        self.db.save_article_score(score_data)

if __name__ == "__main__":
    from psycopg2.extras import RealDictCursor
    scorer = Scorer()
    # In a real app, we'd loop through users. Let's do user 1.
    scorer.score_all_for_user(1)
