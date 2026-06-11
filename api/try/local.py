"""
Semantic Matching V3 — 100% Local Embeddings
- Enrichment : Groq (llama-3.1-8b-instant)
- Embeddings : sentence-transformers all-mpnet-base-v2 (local, no API)
"""

import os
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# ─── CLIENTS ──────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client  = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL   = "llama-3.1-8b-instant"

# Loaded once, runs entirely locally
embed_model = SentenceTransformer("all-mpnet-base-v2")

# ─── USER PROFILE ─────────────────────────────────────────

USER_INTERESTS_RAW = [
    "artificial intelligence",
    "startups",
    "tech innovation"
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
    """Local embedding via all-mpnet-base-v2 — no API call"""
    return embed_model.encode(text, normalize_embeddings=True)


def get_article_embedding(article: dict) -> np.ndarray:
    """Title + summary embedded separately and combined for better semantic coverage"""
    emb_title   = get_embedding(article["title"])
    emb_summary = get_embedding(article["summary"])
    combined = (emb_title * 0.4) + (emb_summary * 0.6)
    norm = np.linalg.norm(combined)
    return combined / norm if norm else combined


def generate_user_topics(interests: list) -> list:
    """Generate generic topic domains from user interests via Groq"""
    interests_str = ", ".join(interests)
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a thematic domain classifier. "
                    "Respond ONLY with a comma-separated list of short domain labels. "
                    "No sentences, no explanations."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Given these user interests: {interests_str}\n"
                    f"Generate 5 to 8 generic topic domains from this list: "
                    f"technology, business, science, politics, sport, health, finance, "
                    f"environment, culture, education, entrepreneurship, computer science.\n"
                    f"Format: topic1, topic2, topic3, ..."
                )
            }
        ],
        max_tokens=100,
        temperature=0.2
    )
    raw = response.choices[0].message.content.strip()
    return [t.strip().lower() for t in raw.split(",") if t.strip()]


def enrich_interest_with_llm(interest: str) -> str:
    """Semantic enrichment of a user interest via Groq"""
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert in semantic enrichment and keyword generation.\n"
                    "Your task is to expand a topic by adding:\n"
                    "- synonyms\n"
                    "- associated concepts\n"
                    "- related fields\n"
                    "- corresponding topics\n"
                    "- sub-domains\n"
                    "- related technologies\n"
                    "- relevant jobs and roles\n"
                    "- major companies or key players\n"
                    "- both English terms and common abbreviations\n\n"
                    "Respond ONLY with a comma-separated list of keywords.\n"
                    "No sentences, no comments, no numbering, no formatting."
                )
            },
            {
                "role": "user",
                "content": (
                    f'Topic: "{interest}"\n\n'
                    "Generate between 50 and 60 highly relevant keywords strongly related to this topic.\n"
                    "Keywords should be useful for article search, content recommendation, "
                    "and semantic matching.\n\n"
                    "Expected format:\n"
                    "keyword 1, keyword 2, keyword 3, ..."
                )
            }
        ],
        temperature=0.3,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(np.dot(v1, v2) / norm) if norm else 0.0


def score_article_multidim(article: dict,
                            interest_embeddings: list,
                            article_embedding: np.ndarray,
                            topic_embeddings: list) -> dict:
    """Multi-dimensional scoring — optimized version"""

    # Dimension 1 — weighted max + mean (reduces false positives)
    scores = [cosine_similarity(article_embedding, ie) for ie in interest_embeddings]
    semantic = (max(scores) * 0.7) + (float(np.mean(scores)) * 0.3)

    # Dimension 2 — gradual semantic topic match (replaces binary 0/1)
    topic_scores = [
        cosine_similarity(te, ie)
        for te in topic_embeddings
        for ie in interest_embeddings
    ]
    topic_match = max(topic_scores) if topic_scores else 0.0

    # Dimension 3 — global importance
    importance = article["importance"] / 10.0

    # Final score
    final = (semantic * 0.6) + (topic_match * 0.2) + (importance * 0.2)

    return {
        "semantic":    round(semantic, 3),
        "topic_match": round(topic_match, 3),
        "importance":  round(importance, 3),
        "final":       round(final, 3)
    }


# ─── MAIN ─────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  SEMANTIC MATCHING V3 — LOCAL (all-mpnet-base-v2) + GROQ")
    print("=" * 65)

    # ── Step 1: Interest enrichment via Groq ──
    print(f"\n👤 Raw interests: {', '.join(USER_INTERESTS_RAW)}")
    print(f"\n🧠 Enriching interests via Groq ({GROQ_MODEL})...\n")

    enriched_interests = []
    for interest in USER_INTERESTS_RAW:
        enriched = enrich_interest_with_llm(interest)
        enriched_interests.append(enriched)
        print(f"   '{interest}'\n   → {enriched[:120]}...\n")

    # ── Step 2: Topic generation via Groq ──
    print("🏷️  Generating user topics via Groq...")
    user_topics = generate_user_topics(USER_INTERESTS_RAW)
    print(f"   → Detected topics: {user_topics}\n")

    # ── Step 3: Profile embeddings (local) ──
    print("⏳ Generating profile embeddings (local)...")
    interest_embeddings = []
    for enriched in enriched_interests:
        emb = get_embedding(enriched)
        interest_embeddings.append(emb)
        print(f"   ✓ vector of {len(emb)} dimensions generated")

    # ── Step 4: Topic embeddings (local) ──
    print("\n⏳ Generating topic embeddings...")
    topic_embeddings = [get_embedding(t) for t in user_topics]
    print(f"   ✓ {len(topic_embeddings)} topics embedded")

    # ── Step 5: Article scoring ──
    print("\n⏳ Scoring articles (title + summary separately)...\n")
    print("-" * 65)

    results = []
    for article in ARTICLES:
        article_emb = get_article_embedding(article)
        scores = score_article_multidim(
            article, interest_embeddings, article_emb, topic_embeddings
        )
        results.append({**article, **scores})

    # ── Step 6: Dynamic thresholds ──
    all_scores = [r["final"] for r in results]
    mean_s = float(np.mean(all_scores))
    std_s  = float(np.std(all_scores))
    SEUIL_HAUT = round(mean_s + 0.5 * std_s, 3)
    SEUIL_BAS  = round(mean_s - 0.2 * std_s, 3)
    print(f"📐 Dynamic thresholds — μ={mean_s:.3f} σ={std_s:.3f}")
    print(f"   🟢 Highly relevant : >= {SEUIL_HAUT}")
    print(f"   🟡 Relevant        : >= {SEUIL_BAS}")
    print(f"   🔴 Filtered        :  < {SEUIL_BAS}\n")

    # ── Step 7: Display results ──
    results_sorted = sorted(results, key=lambda x: x["final"], reverse=True)

    print(f"{'Final':<7} {'Semant':<8} {'Topic':<7} {'Import':<8} {'Label':<20} Title")
    print("-" * 65)

    for r in results_sorted:
        f = r["final"]
        if f >= SEUIL_HAUT:
            label = "🟢 highly relevant"
        elif f >= SEUIL_BAS:
            label = "🟡 relevant"
        else:
            label = "🔴 not relevant"

        title = r["title"][:30] + "..." if len(r["title"]) > 30 else r["title"]
        print(f"{f:<7} {r['semantic']:<8} {r['topic_match']:<7} {r['importance']:<8} {label:<20} {title}")
        print(f"        Expected: {r['expected']}\n")

    # ── Summary ──
    print("-" * 65)
    affiches = [r for r in results if r["final"] >= SEUIL_BAS]
    filtres  = [r for r in results if r["final"] < SEUIL_BAS]

    print(f"\n📊 Summary:")
    print(f"   🟢 Shown in feed : {len(affiches)} / {len(ARTICLES)}")
    print(f"   🔴 Filtered out  : {len(filtres)} / {len(ARTICLES)}")

    print(f"\n✅ User feed:")
    for r in sorted(affiches, key=lambda x: x["final"], reverse=True):
        print(f"   {r['final']} — {r['title']}")

    print(f"\n❌ Filtered articles:")
    for r in sorted(filtres, key=lambda x: x["final"], reverse=True):
        print(f"   {r['final']} — {r['title']}")


if __name__ == "__main__":
    main()