# FeedMe 📰

> An AI-powered, personalized news aggregator that curates content based on your interests and reading habits.

FeedMe is a full-stack web application that continuously ingests articles from configurable RSS feeds, analyzes them with a Large Language Model (Groq/Llama), and surfaces the most relevant content through two personalized feeds: **For You** and **Trending**.

---

## ✨ Features

| Feature | Description |
|---|---|
| **AI Content Analysis** | Each article is processed by an LLM to extract topics, generate summaries, analysis, and commentary |
| **Personalized Feed** | A `for_you_score` is computed per user by matching article topics against user interests via semantic similarity |
| **Trending Feed** | A `trending_score` is computed globally based on topic popularity, content quality, and recency |
| **Automated Ingestion** | A background scheduler runs the full pipeline (fetch → process → score) every hour automatically on server start |
| **Interest Inference** | User interests are both manually defined and auto-inferred from reading behavior |
| **Per-source Article Limit** | Each feed is capped at `LIMIT_PER_SOURCE` articles to ensure source diversity |
| **Read Tracking** | Articles the user has read are marked and excluded from feeds |

---

## 🏗️ Architecture

```
feedme/
├── api/                         # Flask Backend
│   ├── src/
│   │   ├── app.py               # App factory, blueprint registration + scheduler start
│   │   ├── schema.sql           # PostgreSQL schema + seed data
│   │   ├── db.py                # DBManager — all DB interactions
│   │   ├── pipeline.py          # Ingestion entry point
│   │   ├── rss_fetcher.py       # RSS parsing, scraping, LLM extraction
│   │   ├── processor.py         # ArticleProcessor — Groq AI analysis
│   │   ├── scorer.py            # Scorer — semantic scoring per user
│   │   ├── scheduler.py         # Background thread: runs full pipeline every hour
│   │   ├── blueprints/
│   │   │   ├── articles.py      # /api/articles — feed + detail endpoints
│   │   │   ├── users.py         # /api/users — profile & interests endpoints
│   │   │   └── sources.py       # /api/sources — (unused, kept for reference)
│   │   └── utils/
│   │       ├── llm.py           # LLMService (Groq API wrapper)
│   │       ├── scraper.py       # Article content scraper
│   │       └── text.py          # normalize_url, make_id, clean_title
│   └── .env                     # Environment variables
│
└── frontend/                    # React Frontend (Vite)
    └── src/
        ├── App.jsx              # Router + auth guard
        ├── main.jsx             # Entry point + providers
        ├── index.css            # Global design system (glassmorphism)
        ├── pages/
        │   ├── Login.jsx        # User login/selection
        │   ├── ForYou.jsx       # Personalized feed (score ≥ 0.65)
        │   ├── Trending.jsx     # Trending feed (score ≥ 0.70)
        │   ├── ArticleDetail.jsx # Full article view with AI commentary
        │   └── Profile.jsx      # User profile, interests, RSS management
        └── components/
            └── profile/
                └── RSSSourceManager.jsx  # RSS feed CRUD UI component
```

---

## 🗄️ Database Schema

```
articles ──< article_topics >── topics

users ──< user_interests
      ──< user_reads ──> articles
      ──< article_scores ──> articles
```

### Tables

| Table | Description |
|---|---|
| `articles` | Core article store: content, metadata, AI scores |
| `topics` | Unique topics with JSONB embeddings |
| `article_topics` | Many-to-many: articles ↔ topics |
| `users` | Registered users |
| `user_interests` | Per-user topics (manual or inferred) with weights |
| `user_reads` | Read history |
| `article_scores` | Per-user scoring: `for_you_score`, `trending_score`, `semantic_max_sim` |

---

## 🔌 API Reference

### Articles — `/api/articles`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/for-you/<user_id>` | Returns articles scored for a specific user (`for_you_score ≥ 0.65`) |
| `GET` | `/trending/<user_id>` | Returns trending articles (`trending_score ≥ 0.70`) |
| `GET` | `/<article_id>` | Full article details + AI commentary |
| `POST` | `/<article_id>/read` | Mark article as read for a user |

### Users — `/api/users`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/<user_id>` | Get user profile + stats |
| `GET` | `/<user_id>/interests` | List user interests (manual + inferred) |
| `POST` | `/<user_id>/interests` | Add a new interest |
| `DELETE` | `/<user_id>/interests/<name>` | Remove an interest |
| `POST` | `/<user_id>/sync` | Trigger scoring for all unscored articles |

> The `/api/sources` blueprint is kept for reference but RSS feeds are now managed as a hardcoded list in `rss_fetcher.py`.

---

## ⚙️ AI Pipeline

The ingestion pipeline runs in three stages:

```
RSS_SOURCES (hardcoded list in rss_fetcher.py)
        │
        ▼
  [Scheduler] — runs every hour automatically on flask run
        │
        ▼
  [pipeline.run()]
        │
        ├── Step 1: ArticleProcessor (Backlog)
        │   └── Clear old pending articles
        │
        ├── Step 2: RSSFetcher
        │   ├── feedparser.parse(url)        # Parse RSS entries
        │   ├── normalize_url(url)           # Strip tracking params → stable ID
        │   ├── scrape_article_content(url)  # Scrape full article text
        │   └── LLMService.extract(...)      # Groq/Llama: topics, summary, metadata
        │
        └── Step 3: ArticleProcessor (New)
            └── AI analysis, quality scores, commentary
```

### Scoring

- **`for_you_score`**: Blends semantic similarity (cosine of interest vs. topic embeddings) with global quality/relevance. Threshold: **≥ 0.65**
- **`trending_score`**: Based on topic popularity across readers + content quality + recency. Threshold: **≥ 0.70**

### AI Prompting (Groq/Llama 3.1)
- Extraction: topics, summary, author, publication date from raw HTML
- Analysis: rubric-based scoring for `global_relevance` (0.1–1.0) and `content_quality` (0.1–1.0), AI explanation, and journalistic commentary

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL** (local or remote)
- A **Groq API key** (free tier available at [console.groq.com](https://console.groq.com))

### 1. Clone the repository

```bash
git clone https://github.com/your-org/feedme.git
cd feedme
```

### 2. Backend Setup

```bash
cd api
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pdm install
```

Create a `.env` file in `api/`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

DB_NAME=feedme
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

Start the Flask server:

```bash
flask run
```

The API will be available at `http://localhost:5000`.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

### 4. Pipeline & Scheduling

The ingestion pipeline runs **automatically** in the background when you start Flask. It executes every **60 minutes**:

1. Fetches new articles from all RSS sources in `RSS_SOURCES`
2. Processes each article with the AI (topics, summaries, scoring)

> **Note:** Groq's free tier has rate limits. The pipeline includes sleep delays between requests to stay within limits.

---

## 🎛️ Configuration

| Variable | Location | Description |
|---|---|---|
| `GROQ_API_KEY` | `api/.env` | API key for the Groq LLM service |
| `GEMINI_API_KEY` | `api/.env` | API key for the Google Gemini LLM service |
| `DB_NAME` | `api/.env` | PostgreSQL database name |
| `DB_USER` | `api/.env` | PostgreSQL username |
| `DB_PASSWORD` | `api/.env` | PostgreSQL password |
| `DB_HOST` | `api/.env` | Database host (default: `localhost`) |
| `DB_PORT` | `api/.env` | Database port (default: `5432`) |
| `LIMIT_PER_SOURCE` | `api/src/rss_fetcher.py` | Max articles per RSS feed per run (default: `20`) |
| `RSS_SOURCES` | `api/src/rss_fetcher.py` | Hardcoded list of RSS feed names + URLs |
| Scheduler interval | `api/src/scheduler.py` | Pipeline run interval (default: `3600` seconds) |

---

## 🖥️ Frontend Pages

| Page | Route | Description |
|---|---|---|
| Login | `/login` | User selection screen |
| For You | `/` | Personalized article feed |
| Trending | `/trending` | Globally trending articles |
| Article Detail | `/article/:id` | Full article + AI commentary |
| Profile | `/profile` | User info, interests manager, RSS source manager |

---

## 🛠️ Tech Stack

**Backend**
- [Flask](https://flask.palletsprojects.com/) — REST API
- [PostgreSQL](https://www.postgresql.org/) — Primary database
- [psycopg2](https://www.psycopg.org/) — PostgreSQL adapter
- [feedparser](https://feedparser.readthedocs.io/) — RSS/Atom feed parsing
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML scraping
- [Groq API](https://groq.com/) — LLM inference (Llama 3.1)
- [APScheduler](https://apscheduler.readthedocs.io/) — Background task scheduler

**Frontend**
- [React 18](https://react.dev/) — UI framework
- [Vite](https://vitejs.dev/) — Build tool
- [React Router v6](https://reactrouter.com/) — Client-side routing
- [Lucide React](https://lucide.dev/) — Icon library
- Vanilla CSS — Custom glassmorphism design system

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
