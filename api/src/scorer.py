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
        # Fallback to batch if possible, but keep for legacy
        return self.get_embeddings_batch([text])[0]

    def get_embeddings_batch(self, texts: list) -> list:
        """Batch get embeddings from Gemini. Limit texts to ~100 per call."""
        if not texts:
            return []
        
        print(f"   [Gemini API] Batch embedding {len(texts)} items...")
        try:
            # google-genai supports list of contents for embed_content
            result = self.gemini_client.models.embed_content(
                model=self.MODEL_EMBED,
                contents=texts
            )
            # result.embeddings is a list of objects with a values attribute
            return [emb.values for emb in result.embeddings]
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"      [Gemini API] Rate limit hit. {e}")
                # Re-throw for higher level handling
                raise e
            print(f"      [Gemini API Error] {e}")
            return [None] * len(texts)
        
        # Generate embeddings for enriched interests
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

    def score_all_for_user(self, user_id, only_unscored=True):
        """Score articles for a specific user using topic-based matching"""
        # 1. Get user interests and ensure they have embeddings
        interests = self.db.get_user_interests(user_id)
        
        missing_interest_names = [i['interest_name'] for i in interests if not i['embedding']]
        if missing_interest_names:
            print(f"👤 User {user_id} has {len(missing_interest_names)} missing interest embeddings. Batching...")
            embs = self.get_embeddings_batch(missing_interest_names)
            for name, emb in zip(missing_interest_names, embs):
                if emb:
                    self.db.save_interest_embedding(user_id, name, emb)
            # Re-fetch with embeddings
            interests = self.db.get_user_interests(user_id)
            
        interest_embs = [i['embedding'] for i in interests if i['embedding']]

        # 2. Get processed articles from the last 7 days
        if only_unscored:
            query = """
                SELECT a.* FROM articles a
                WHERE a.status = 'processed' 
                  AND a.published_at > NOW() - INTERVAL '7 days'
                  AND NOT EXISTS (
                    SELECT 1 FROM article_scores s 
                    WHERE s.article_id = a.id AND s.user_id = %s
                  )
            """
            params = (user_id,)
        else:
            query = "SELECT * FROM articles WHERE status = 'processed' AND published_at > NOW() - INTERVAL '7 days'"
            params = ()

        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            articles = cur.fetchall()

        if not articles:
            print(f"✅ No new articles to score for user {user_id}.")
            return

        # 3. Ensure all topics for THESE articles have embeddings
        # Collect all unique topic IDs/names that need embeddings
        all_topics_dict = {} # name -> id
        missing_topic_ids = {} # id -> name
        
        for art in articles:
            topics = self.db.get_article_topics(art['id'])
            for t in topics:
                if not t['embedding']:
                    missing_topic_ids[t['id']] = t['name']
        
        if missing_topic_ids:
            t_ids = list(missing_topic_ids.keys())
            t_names = list(missing_topic_ids.values())
            print(f"🏷️  System has {len(t_names)} missing topic embeddings. Batching...")
            
            # Group into batches of 50 to be extra safe with Gemini free tier (100 RPM)
            for i in range(0, len(t_names), 50):
                batch_names = t_names[i:i+50]
                batch_ids = t_ids[i:i+50]
                embs = self.get_embeddings_batch(batch_names)
                for tid, emb in zip(batch_ids, embs):
                    if emb:
                        self.db.save_topic_embedding(tid, emb)
                if i + 50 < len(t_names):
                    time.sleep(2) # Breath between batches

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
        
        # 1. Pre-fetch ALL missing interest embeddings for ALL users
        all_missing_interests = {} # (user_id, name) -> user_id
        for u in users:
            interests = self.db.get_user_interests(u['id'])
            for i in interests:
                if not i['embedding']:
                    all_missing_interests[(u['id'], i['interest_name'])] = u['id']
        
        if all_missing_interests:
            print(f"👥 System has {len(all_missing_interests)} missing user interest embeddings. Batching...")
            items = list(all_missing_interests.keys())
            names = [item[1] for item in items]
            
            for i in range(0, len(names), 50):
                batch_names = names[i:i+50]
                batch_items = items[i:i+50]
                embs = self.get_embeddings_batch(batch_names)
                for (uid, name), emb in zip(batch_items, embs):
                    if emb:
                        self.db.save_interest_embedding(uid, name, emb)
                if i + 50 < len(names):
                    time.sleep(1)

        # 2. Ensure article topics have embeddings
        topics = self.db.get_article_topics(article_id)
        missing_topics = [(t['id'], t['name']) for t in topics if not t['embedding']]
        if missing_topics:
            print(f"🏷️  Article {article_id} has {len(missing_topics)} missing topic embeddings. Batching...")
            embs = self.get_embeddings_batch([t[1] for t in missing_topics])
            for (tid, name), emb in zip(missing_topics, embs):
                if emb:
                    self.db.save_topic_embedding(tid, emb)

        # 3. Proceed with scoring
        for u in users:
            # Re-fetch interests with embeddings
            interests = self.db.get_user_interests(u['id'])
            interest_embs = [i['embedding'] for i in interests if i['embedding']]
            self._score_single(u['id'], art, interest_embs)

    def _score_single(self, user_id, art, interest_embs):
        """Helper to score one article for one user"""
        # 1. Get article topics and their embeddings
        topics = self.db.get_article_topics(art['id'])
        topic_embs = [t['embedding'] for t in topics if t['embedding']]

        # If somehow we still have missing embs (e.g. batch failed), skip them or fetch one-off
        # But score_all_for_user should have handled this.

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
        for_you = (max_sim * 0.7) + (relevance * 0.2) + (quality * 0.1)
        
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
