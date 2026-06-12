-- Normalized News Pipeline Schema

-- 1. Articles Table
CREATE TABLE IF NOT EXISTS articles (
    id VARCHAR(12) PRIMARY KEY,
    url TEXT UNIQUE,
    source_id INTEGER,
    title TEXT,
    content TEXT,
    summary TEXT,
    image_url TEXT,
    author TEXT,
    published_at TIMESTAMP,
    global_relevance FLOAT,
    content_quality FLOAT,
    popularity_score FLOAT,
    ai_explanation TEXT,
    ai_analysis TEXT,
    ai_commentary TEXT,
    status VARCHAR(20) DEFAULT 'pending'
);

-- 2. Topics Table (Unique topics with embeddings)
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    embedding JSONB
);

-- 3. Article-Topics Link (Many-to-Many)
CREATE TABLE IF NOT EXISTS article_topics (
    article_id VARCHAR(12) REFERENCES articles(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, topic_id)
);

-- 4. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE
);

-- 5. User Interests Table
CREATE TABLE IF NOT EXISTS user_interests (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    interest_name VARCHAR(100),
    weight FLOAT DEFAULT 1.0, -- 1.0 for manual, 0.2 for inferred
    source VARCHAR(20) DEFAULT 'manual', -- 'manual', 'inferred'
    embedding JSONB,
    PRIMARY KEY (user_id, interest_name)
);

-- 6. User Reads Table (Tracking history)
CREATE TABLE IF NOT EXISTS user_reads (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    article_id VARCHAR(12) REFERENCES articles(id) ON DELETE CASCADE,
    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, article_id)
);

-- 7. Article Scores Table
CREATE TABLE IF NOT EXISTS article_scores (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    article_id VARCHAR(12) REFERENCES articles(id) ON DELETE CASCADE,
    for_you_score FLOAT,
    trending_score FLOAT,
    semantic_max_sim FLOAT,
    PRIMARY KEY (user_id, article_id)
);

-- ─── SEED DATA ──────────────────────────────────────────

-- Insert test users
INSERT INTO users (name, email) VALUES 
('Alice Tech', 'alice@example.com'),
('Bob Business', 'bob@example.com')
ON CONFLICT DO NOTHING;

-- Insert test interests
INSERT INTO user_interests (user_id, interest_name) VALUES 
(1, 'Artificial Intelligence'),
(1, 'SpaceX'),
(1, 'Generative AI'),
(2, 'Stock Market'),
(2, 'Venture Capital'),
(2, 'Technology')
ON CONFLICT DO NOTHING;
