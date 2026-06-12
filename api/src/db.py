import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv
load_dotenv()
class DBManager:
    def __init__(self):
        self.conn = None
        self.connect()
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "news_db"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432")
            )
            self.conn.autocommit = True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    def init_db(self):
        """Initialize database using schema.sql"""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        
        with self.conn.cursor() as cur:
            cur.execute(schema_sql)
            print("Database initialized with normalized schema.")
    def insert_article(self, article_data: dict):
        query = """
            INSERT INTO articles (id, url, title, content, image_url, author, published_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """
        params = (
            article_data['id'],
            article_data['url'],
            article_data['title'],
            article_data['content'],
            article_data.get('image_url'),
            article_data.get('author'),
            article_data['published_at'],
            article_data.get('status', 'pending')
        )
        with self.conn.cursor() as cur:
            cur.execute(query, params)
    def article_exists(self, article_id: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM articles WHERE id = %s", (article_id,))
            return cur.fetchone() is not None
        
    def get_pending_articles(self, limit=10):
        query = "SELECT * FROM articles WHERE status = 'pending' LIMIT %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            return cur.fetchall()
    def get_or_create_topic(self, topic_name: str):
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO topics (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (topic_name,))
            cur.execute("SELECT id FROM topics WHERE name = %s", (topic_name,))
            return cur.fetchone()[0]
    def link_article_to_topic(self, article_id, topic_id, is_global=False):
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO article_topics (article_id, topic_id, is_global) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (article_id, topic_id, is_global))
    def update_article_enrichment(self, article_id, data: dict):
        query = """
            UPDATE articles 
            SET summary = %s, global_relevance = %s, content_quality = %s, 
                popularity_score = %s, status = 'processed'
            WHERE id = %s
        """
        params = (
            data['summary'],
            data['global_relevance'],
            data['content_quality'],
            data['popularity_score'],
            article_id
        )
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            
        # Handle specific topics
        for t_name in data.get('topics', []):
            t_id = self.get_or_create_topic(t_name)
            self.link_article_to_topic(article_id, t_id, is_global=False)

        # Handle global topics (for following)
        for t_name in data.get('global_topics', []):
            t_id = self.get_or_create_topic(t_name)
            self.link_article_to_topic(article_id, t_id, is_global=True)

    def get_article_topics(self, article_id):
        query = """
            SELECT t.id, t.name, t.embedding, at.is_global FROM topics t
            JOIN article_topics at ON t.id = at.topic_id
            WHERE at.article_id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (article_id,))
            return cur.fetchall()

    def update_article_analysis(self, article_id, data: dict):
        def stringify(val):
            if val is None:
                return None
            if isinstance(val, dict):
                # Recursively extract values and join them
                return "\n\n".join([stringify(v) for v in val.values() if v])
            if isinstance(val, list):
                return "\n\n".join([stringify(v) for v in val if v])
            return str(val).strip()

        query = """
            UPDATE articles 
            SET ai_explanation = %s, ai_analysis = %s, ai_commentary = %s
            WHERE id = %s
        """
        params = (
            stringify(data.get('ai_explanation')),
            stringify(data.get('ai_analysis')),
            stringify(data.get('ai_commentary')),
            article_id
        )
        with self.conn.cursor() as cur:
            cur.execute(query, params)
    def save_topic_embedding(self, topic_id, embedding):
        with self.conn.cursor() as cur:
            cur.execute("UPDATE topics SET embedding = %s WHERE id = %s", (Json(embedding), topic_id))
    def save_interest_embedding(self, user_id, interest_name, embedding):
        with self.conn.cursor() as cur:
            cur.execute("UPDATE user_interests SET embedding = %s WHERE user_id = %s AND interest_name = %s", (Json(embedding), user_id, interest_name))
    def get_users(self):
        query = "SELECT * FROM users"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()
    def get_user_interests(self, user_id):
        query = "SELECT * FROM user_interests WHERE user_id = %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_id,))
            return cur.fetchall()
    def save_article_score(self, score_data: dict):
        query = """
            INSERT INTO article_scores (user_id, article_id, for_you_score, trending_score, semantic_max_sim)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, article_id) DO UPDATE 
            SET for_you_score = EXCLUDED.for_you_score,
                trending_score = EXCLUDED.trending_score,
                semantic_max_sim = EXCLUDED.semantic_max_sim
        """
        params = (
            score_data['user_id'],
            score_data['article_id'],
            score_data['for_you_score'],
            score_data['trending_score'],
            score_data['semantic_max_sim']
        )
        with self.conn.cursor() as cur:
            cur.execute(query, params)
    def get_for_you_articles(self, user_id, limit=20):
        query = """
            SELECT a.*, TO_CHAR(a.published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as published_at, 
                   s.for_you_score, s.trending_score
            FROM articles a
            JOIN article_scores s ON a.id = s.article_id
            WHERE s.user_id = %s AND a.status = 'processed' AND s.for_you_score >= 0.65
            ORDER BY (a.published_at AT TIME ZONE 'UTC')::DATE DESC, s.for_you_score DESC, s.trending_score DESC
            LIMIT %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_id, limit))
            return cur.fetchall()
            
    def get_trending_articles(self, limit=20, user_id=None):
        if user_id:
            query = """
                SELECT a.*, TO_CHAR(a.published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as published_at, 
                       COALESCE(s.for_you_score, 0) as for_you_score, 
                       COALESCE(s.trending_score, 0) as trending_score
                FROM articles a
                LEFT JOIN article_scores s ON a.id = s.article_id AND s.user_id = %s
                WHERE a.status = 'processed' AND s.trending_score >= 0.70
                ORDER BY (a.published_at AT TIME ZONE 'UTC')::DATE DESC, s.trending_score DESC
                LIMIT %s
            """
            params = (user_id, limit)
        else:
            query = """
                SELECT *, 0 as for_you_score, 0 as trending_score FROM articles 
                WHERE status = 'processed'
                ORDER BY published_at::DATE DESC, popularity_score DESC
                LIMIT %s
            """
            params = (limit,)
            
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    def get_article_by_id(self, article_id, user_id=None):
        if user_id:
            query = """
                SELECT a.*, TO_CHAR(a.published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as published_at, 
                       COALESCE(s.for_you_score, 0) as for_you_score, 
                       COALESCE(s.trending_score, 0) as trending_score
                FROM articles a
                LEFT JOIN article_scores s ON a.id = s.article_id AND s.user_id = %s
                WHERE a.id = %s
            """
            params = (user_id, article_id)
        else:
            query = """
                SELECT *, TO_CHAR(published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as published_at 
                FROM articles WHERE id = %s
            """
            params = (article_id,)
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()
    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_id,))
            return cur.fetchone()
    def get_user_by_email(self, email):
        query = "SELECT * FROM users WHERE email = %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (email,))
            return cur.fetchone()
    def add_user_interest(self, user_id, interest_name, source='manual', weight=1.0):
        query = """
            INSERT INTO user_interests (user_id, interest_name, source, weight) 
            VALUES (%s, %s, %s, %s) 
            ON CONFLICT (user_id, interest_name) DO UPDATE 
            SET weight = GREATEST(user_interests.weight, EXCLUDED.weight)
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (user_id, interest_name, source, weight))
    def remove_user_interest(self, user_id, interest_name):
        query = "DELETE FROM user_interests WHERE user_id = %s AND interest_name = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (user_id, interest_name))
    def record_article_read(self, user_id, article_id):
        # Record read
        query = "INSERT INTO user_reads (user_id, article_id) VALUES (%s, %s) ON CONFLICT DO NOTHING"
        with self.conn.cursor() as cur:
            cur.execute(query, (user_id, article_id))
            
    def get_user_stats(self, user_id):
        stats = {}
        with self.conn.cursor() as cur:
            # Articles read
            cur.execute("SELECT COUNT(*) FROM user_reads WHERE user_id = %s", (user_id,))
            stats['articles_read'] = cur.fetchone()[0]
            
            # Interests count
            cur.execute("SELECT COUNT(*) FROM user_interests WHERE user_id = %s", (user_id,))
            stats['interests_count'] = cur.fetchone()[0]
            
        return stats

    # ─── RSS SOURCES ─────────────────────────────────────────

    def get_rss_sources(self):
        query = "SELECT * FROM rss_sources ORDER BY name ASC"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def add_rss_source(self, name, url):
        query = "INSERT INTO rss_sources (name, url) VALUES (%s, %s) RETURNING id"
        with self.conn.cursor() as cur:
            cur.execute(query, (name, url))
            return cur.fetchone()[0]

    def delete_rss_source(self, source_id):
        query = "DELETE FROM rss_sources WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (source_id,))

    def update_rss_source(self, source_id, name, url):
        query = "UPDATE rss_sources SET name = %s, url = %s WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (name, url, source_id))
if __name__ == "__main__":
    db = DBManager()
    db.init_db()