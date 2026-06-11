"""
Test matching semantic V3 — Full English
- Groq Llama 3.3 70B for all LLM tasks
- Gemini embedding-001 for vectors only
- Multi-dimensional scoring
"""

import os
import time
import numpy as np
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ─── CLIENTS ──────────────────────────────────────────────
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_client   = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_EMBED    = "gemini-embedding-001"
GROQ_MAIN      = "llama-3.3-70b-versatile"   # main — best quality
GROQ_FAST      = "llama-3.1-8b-instant"       # fast — real-time tasks

# ─── USER PROFILE ─────────────────────────────────────────
USER_INTERESTS_RAW = [
    # "artificial intelligence",
    # "startups",
    # "tech innovation"
    "technology"
]

# ─── ARTICLES (simulated as if already fetched from RSS) ──
ARTICLES = [
    {
        "id": 1,
        "title": "Google unveils Gemini Ultra 3.0, a major leap in machine learning",
        "topic": "technology",
        "summary": "Google has presented Gemini Ultra 3.0, its new large language model based on deep learning and transformer neural networks. This LLM outperforms GPT-4 on all major AI benchmarks and represents a breakthrough in generative artificial intelligence.",
        "importance": 9.0,
        "expected": "✅ highly relevant"
    },
    {
        "id": 2,
        "title": "ChatGPT surpasses 500 million active users worldwide",
        "topic": "technology",
        "summary": "OpenAI announces that ChatGPT, its AI assistant powered by large language models, has reached 500 million active users globally. This milestone reflects the massive adoption of generative AI and LLM-based tools by the general public.",
        "importance": 8.5,
        "expected": "✅ highly relevant"
    },
    {
        "id": 3,
        "title": "French startup raises 10M€ to disrupt logistics industry",
        "topic": "business",
        "summary": "A French startup founded in 2024 has secured 10 million euros in seed funding from venture capital firms to scale its AI-powered logistics optimization platform. European tech entrepreneurship continues to grow strongly.",
        "importance": 6.0,
        "expected": "✅ relevant"
    },
    {
        "id": 4,
        "title": "Tesla Autopilot: AI is redefining autonomous driving",
        "topic": "technology",
        "summary": "Tesla has significantly improved its Autopilot system using new artificial intelligence algorithms and computer vision techniques. Level 4 autonomous driving is approaching thanks to recent advances in machine learning and neural networks.",
        "importance": 7.5,
        "expected": "✅ relevant"
    },
    {
        "id": 5,
        "title": "2028 Olympics: Los Angeles finalizes preparations",
        "topic": "sport",
        "summary": "Los Angeles is making steady progress in preparing for the 2028 Olympic Games. Sports infrastructure, transportation plans, and the Olympic village construction are on track to welcome athletes from around the world.",
        "importance": 5.0,
        "expected": "❌ not relevant"
    },
    {
        "id": 6,
        "title": "Recipe: Classic French caramelized apple tarte tatin",
        "topic": "food",
        "summary": "Discover the traditional recipe for tarte tatin with caramelized apples. A crispy puff pastry base topped with golden butter-cooked apples and brown sugar, creating a delicious and easy-to-make dessert for the whole family.",
        "importance": 2.0,
        "expected": "❌ not relevant"
    },
    {
        "id": 7,
        "title": "European elections: key economic challenges ahead",
        "topic": "politics",
        "summary": "The upcoming European elections are focusing debate on fiscal policy, corporate taxation, and industrial sovereignty of the European Union in relation to the United States and China. Economic competitiveness is at the heart of every campaign.",
        "importance": 7.0,
        "expected": "❌ not relevant"
    },
    {
        "id": 8,
        "title": "Nvidia announces revolutionary AI chip for data centers",
        "topic": "technology",
        "summary": "Nvidia has unveiled the H300 GPU specifically designed for training large AI models in data centers. This chip delivers 4x better performance for deep learning and LLM workloads, marking a major step forward for artificial intelligence infrastructure.",
        "importance": 9.0,
        "expected": "✅ highly relevant"
    },
    {
        "id": 9,
        "title": "Climate change: record temperatures hit Europe this summer",
        "topic": "environment",
        "summary": "Europe experienced its hottest summer on record in 2026, with temperatures exceeding 45°C in several countries. Scientists warn that without urgent action on carbon emissions, extreme heat events will become the new normal by 2040.",
        "importance": 8.0,
        "expected": "❌ not relevant"
    },
    {
        "id": 10,
        "title": "Y Combinator's latest batch features 40% AI startups",
        "topic": "business",
        "summary": "Y Combinator's Summer 2026 batch includes a record 40% of AI-focused startups, reflecting the dominance of artificial intelligence in early-stage venture funding. Founders are building LLM-powered tools across healthcare, legal, and finance sectors.",
        "importance": 7.5,
        "expected": "✅ highly relevant"
    },
]

# ─── FUNCTIONS ────────────────────────────────────────────

def get_embedding(text: str) -> np.ndarray:
    time.sleep(0.3)
    result = gemini_client.models.embed_content(
        model=MODEL_EMBED,
        contents=text
    )
    return np.array(result.embeddings[0].values)


def enrich_interest(interest: str) -> str:
    """Expand a user interest into rich semantic keywords using Groq"""
    response = groq_client.chat.completions.create(
        model=GROQ_MAIN,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a semantic enrichment expert. "
                    "Given a topic, generate a rich list of related keywords, synonyms, "
                    "sub-topics, technologies, companies, roles, and concepts. "
                    "Return ONLY a comma-separated list of keywords. "
                    "No sentences, no explanations, no numbering."
                )
            },
            {
                "role": "user",
                "content": (
                    f'Topic: "{interest}"\n\n'
                    "Generate 50 to 60 highly relevant keywords for semantic search "
                    "and content recommendation. Include both technical and general terms.\n\n"
                    "Format: keyword1, keyword2, keyword3, ..."
                )
            }
        ],
        temperature=0.3,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()


def detect_user_topics(interests: list) -> list:
    """Generate broad topic categories from user interests"""
    response = groq_client.chat.completions.create(
        model=GROQ_FAST,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a topic classifier. "
                    "Return ONLY a comma-separated list of topic labels. "
                    "No sentences, no explanations."
                )
            },
            {
                "role": "user",
                "content": (
                    f"User interests: {', '.join(interests)}\n\n"
                    "Return 5 to 8 broad topic categories from this list only: "
                    "technology, business, science, politics, sport, health, "
                    "finance, environment, culture, education, food.\n\n"
                    "Format: topic1, topic2, topic3"
                )
            }
        ],
        max_tokens=80,
        temperature=0.1
    )
    raw = response.choices[0].message.content.strip()
    return [t.strip().lower() for t in raw.split(",") if t.strip()]


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(np.dot(v1, v2) / norm) if norm else 0.0


def score_article(article: dict, interest_embs: list,
                  article_emb: np.ndarray, user_topics: list) -> dict:
    # Dimension 1 — Semantic similarity (enriched embeddings)
    semantic = max(cosine_similarity(article_emb, ie) for ie in interest_embs)

    # Dimension 2 — Direct topic match
    topic = 1.0 if article["topic"] in user_topics else 0.0

    # Dimension 3 — Global importance
    importance = article["importance"] / 10.0

    final = (semantic * 0.55) + (topic * 0.1) + (importance * 0.35)

    return {
        "semantic":   round(semantic, 3),
        "topic":      round(topic, 3),
        "importance": round(importance, 3),
        "final":      round(final, 3)
    }


# ─── MAIN ─────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  SEMANTIC MATCHING TEST V3 — FULL ENGLISH")
    print("  Groq Llama 3.3 70B (LLM) + Gemini embedding-001 (vectors)")
    print("=" * 70)

    # Step 1 — Enrich user interests via Groq
    print(f"\n👤 Raw interests: {', '.join(USER_INTERESTS_RAW)}")
    print(f"\n🧠 Enriching interests with Groq ({GROQ_MAIN})...\n")

    enriched_list = []
    for interest in USER_INTERESTS_RAW:
        enriched = enrich_interest(interest)
        enriched_list.append(enriched)
        preview = enriched[:100].strip()
        print(f"   '{interest}'\n   → {preview}...\n")

    # Step 2 — Detect user topics
    print(f"🏷️  Detecting topic categories ({GROQ_FAST})...")
    user_topics = detect_user_topics(USER_INTERESTS_RAW)
    print(f"   → Detected topics: {user_topics}\n")

    # Step 3 — Generate embeddings for enriched interests
    print("⏳ Generating interest embeddings (Gemini)...")
    interest_embs = []
    for enriched in enriched_list:
        emb = get_embedding(enriched)
        interest_embs.append(emb)
        print(f"   ✓ vector {len(emb)} dimensions")

    # Step 4 — Score all articles
    print("\n⏳ Scoring articles...\n")
    results = []
    for article in ARTICLES:
        text = (
            f"title: {article['title']}\n"
            f"topic: {article['topic']}\n"
            f"content: {article['summary']}"
        )
        emb    = get_embedding(text)
        scores = score_article(article, interest_embs, emb, user_topics)
        results.append({**article, **scores})

    # Step 5 — Display results
    results_sorted = sorted(results, key=lambda x: x["final"], reverse=True)

    THRESHOLD_HIGH = 0.73
    THRESHOLD_LOW  = 0.65

    print(f"{'Final':<7} {'Sem':<7} {'Top':<6} {'Imp':<7} {'Label':<20} Title")
    print("-" * 70)

    for r in results_sorted:
        f = r["final"]
        if f >= THRESHOLD_HIGH:
            label = "🟢 highly relevant"
        elif f >= THRESHOLD_LOW:
            label = "🟡 relevant"
        else:
            label = "🔴 not relevant"

        title = r["title"][:32] + "..." if len(r["title"]) > 32 else r["title"]
        print(f"{f:<7} {r['semantic']:<7} {r['topic']:<6} {r['importance']:<7} {label:<20} {title}")
        print(f"        Expected: {r['expected']}\n")

    # Step 6 — Summary
    print("-" * 70)
    shown    = [r for r in results if r["final"] >= THRESHOLD_LOW]
    filtered = [r for r in results if r["final"] < THRESHOLD_LOW]

    print(f"\n📊 Results: {len(shown)} shown / {len(filtered)} filtered out of {len(ARTICLES)}\n")

    print("✅ User feed:")
    for r in sorted(shown, key=lambda x: x["final"], reverse=True):
        print(f"   {r['final']} — {r['title']}")

    print("\n❌ Filtered out:")
    for r in sorted(filtered, key=lambda x: x["final"], reverse=True):
        print(f"   {r['final']} — {r['title']}")

    # Step 7 — Accuracy check
    print(f"\n{'='*70}")
    print("  ACCURACY CHECK")
    print(f"{'='*70}")
    correct = 0
    for r in results:
        is_shown     = r["final"] >= THRESHOLD_LOW
        should_shown = "✅" in r["expected"]
        match        = is_shown == should_shown
        if match:
            correct += 1
        status = "✓" if match else "✗ WRONG"
        print(f"   {status}  {r['final']}  {r['title'][:45]}")

    accuracy = (correct / len(results)) * 100
    print(f"\n   Accuracy: {correct}/{len(results)} = {accuracy:.0f}%")


if __name__ == "__main__":
    main()