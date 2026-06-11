"""
Test matching sémantique V2 — Améliorations :
1. Profil utilisateur enrichi par LLM (Groq - gratuit)
2. Article représenté par titre + topic + résumé simulé
3. Score multi-dimensions
4. Embeddings via Gemini uniquement
"""

import os
import time
import numpy as np
from google import genai
from groq import Groq
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# ─── CLIENTS ──────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client   = Groq(api_key=GROQ_API_KEY)

MODEL_EMBED = "gemini-embedding-001"
GROQ_MODEL  = "llama-3.1-8b-instant"

# ─── PROFIL UTILISATEUR ───────────────────────────────────

USER_INTERESTS_RAW = [
    "intelligence artificielle",
    # "startups",
    "innovation technologique"
]

# ─── ARTICLES SIMULÉS ─────────────────────────────────────

ARTICLES = [
    {
        "id": 1,
        "title": "Google dévoile Gemini Ultra 3.0",
        "topic": "technologie",
        "summary": """Google présente Gemini Ultra 3.0, son nouveau modèle de langage
        basé sur le deep learning et les transformers. Ce LLM surpasse GPT-4 sur les
        benchmarks IA et représente une avancée majeure pour l intelligence artificielle
        générative et le machine learning.""",
        "importance": 9.0,
        "attendu": "✅ très pertinent"
    },
    {
        "id": 2,
        "title": "ChatGPT dépasse 500 millions d'utilisateurs",
        "topic": "technologie",
        "summary": """OpenAI annonce que ChatGPT, son assistant basé sur les LLM et
        l intelligence artificielle générative, franchit 500 millions d utilisateurs.
        Une adoption massive de l IA et des modèles de langage dans le grand public.""",
        "importance": 8.5,
        "attendu": "✅ très pertinent"
    },
    {
        "id": 3,
        "title": "Une startup lève 10M€ pour révolutionner la logistique",
        "topic": "business",
        "summary": """Une jeune startup française lève 10M€ auprès de fonds de
        capital-risque pour sa solution d optimisation logistique. L entrepreneuriat
        tech et les levées de fonds en seed funding continuent de progresser en Europe.""",
        "importance": 6.0,
        "attendu": "✅ pertinent"
    },
    {
        "id": 4,
        "title": "Tesla autopilot : l'IA redéfinit la conduite autonome",
        "topic": "technologie",
        "summary": """Tesla améliore son autopilot avec de nouveaux algorithmes
        d intelligence artificielle et de computer vision. La conduite autonome
        de niveau 4 se rapproche grâce aux avancées en machine learning et deep learning.""",
        "importance": 7.5,
        "attendu": "✅ pertinent"
    },
    {
        "id": 5,
        "title": "Les Jeux Olympiques 2028 : Los Angeles se prépare",
        "topic": "sport",
        "summary": """Los Angeles finalise ses infrastructures sportives pour les JO 2028.
        Les stades, le village olympique et les plans de transport sont en cours
        de construction pour accueillir les athlètes du monde entier.""",
        "importance": 5.0,
        "attendu": "❌ non pertinent"
    },
    {
        "id": 6,
        "title": "Recette : tarte tatin aux pommes caramélisées",
        "topic": "cuisine",
        "summary": """La recette traditionnelle de la tarte tatin : une pâte feuilletée
        croustillante avec des pommes caramélisées au beurre et au sucre brun.
        Un dessert savoureux et facile pour toute la famille.""",
        "importance": 2.0,
        "attendu": "❌ non pertinent"
    },
    {
        "id": 7,
        "title": "Élections européennes : les enjeux économiques",
        "topic": "politique",
        "summary": """Les élections européennes 2026 cristallisent les débats autour
        des politiques fiscales, de la souveraineté industrielle et des relations
        commerciales entre l Union Européenne, les États-Unis et la Chine.""",
        "importance": 7.0,
        "attendu": "❌ non pertinent"
    },
    {
        "id": 8,
        "title": "Nvidia annonce une puce révolutionnaire pour l'IA",
        "topic": "technologie",
        "summary": """Nvidia présente le GPU H300 pour data centers IA, offrant des
        performances 4x supérieures pour l entraînement de LLM et le deep learning.
        Une avancée majeure pour l intelligence artificielle et le machine learning.""",
        "importance": 9.0,
        "attendu": "✅ très pertinent"
    },
]


# ─── FONCTIONS ────────────────────────────────────────────

def get_embedding(text: str) -> np.ndarray:
    """Embedding via Gemini (utilisé uniquement pour les vecteurs)"""
    time.sleep(0.5)  # éviter rate limit Gemini
    result = gemini_client.models.embed_content(
        model=MODEL_EMBED,
        contents=text
    )
    return np.array(result.embeddings[0].values)


def enrich_interest_with_llm(interest: str) -> str:
    """Enrichissement sémantique d'un centre d'intérêt"""
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un expert en enrichissement sémantique et génération de mots-clés liées à un mot.\n"
                    "Ta mission est d'élargir un sujet en ajoutant :\n"
                    "- synonymes\n"
                    "- concepts associés\n"
                    "- domaines connexes\n"
                    "- topics correspondants\n"
                    "- sous-domaines\n"
                    "- technologies liées\n"
                    "- métiers et rôles concernés\n"
                    "- entreprises ou acteurs majeurs pertinents\n"
                    "- termes français et anglais lorsqu'ils sont couramment utilisés\n\n"
                    "Réponds UNIQUEMENT par une liste de mots-clés séparés par des virgules.\n"
                    "Aucune phrase, aucun commentaire, aucune numérotation, aucun formatage."
                )
            },
            {
                "role": "user",
                "content": (
                    f'Sujet : "{interest}"\n\n'
                    "Génère entre 50 et 60 mots-clés pertinents et très fortement liés au sujet.\n"
                    "Les mots-clés doivent être très utiles pour la recherche d'articles, "
                    "la recommandation de contenu et la recherche sémantique.\n\n"
                    "Format attendu :\n"
                    "mot-clé 1, mot-clé 2, mot-clé 3, ..."
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
                            user_topics: list) -> dict:
    """Score multi-dimensions"""

    # Dimension 1 — Similarité sémantique (embedding enrichi)
    semantic = max(
        cosine_similarity(article_embedding, ie)
        for ie in interest_embeddings
    )

    # Dimension 2 — Match direct topic déclaré
    topic_match = 1.0 if article["topic"] in user_topics else 0.0

    # Dimension 3 — Importance mondiale
    importance = article["importance"] / 10.0

    # Score final
    final = (semantic * 0.9) + (topic_match * 0.0) + (importance * 0.1)

    return {
        "semantic":    round(semantic, 3),
        "topic_match": round(topic_match, 3),
        "importance":  round(importance, 3),
        "final":       round(final, 3)
    }


# ─── MAIN ─────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  TEST MATCHING SÉMANTIQUE V2 — GROQ (enrichissement) + GEMINI (embeddings)")
    print("=" * 65)

    # ── Étape 1 : Enrichissement via Groq ──
    print(f"\n👤 Centres d'intérêt bruts : {', '.join(USER_INTERESTS_RAW)}")
    print(f"\n🧠 Enrichissement via Groq ({GROQ_MODEL})...\n")

    enriched_interests = []
    user_topics = []

    for interest in USER_INTERESTS_RAW:
        enriched = enrich_interest_with_llm(interest)
        enriched_interests.append(enriched)
        user_topics.append(interest)
        print(f"   '{interest}'\n   → {enriched[:120]}...\n")

    # ── Étape 2 : Embeddings Gemini des profils enrichis ──
    print("⏳ Génération embeddings profil (Gemini)...")
    interest_embeddings = []
    for enriched in enriched_interests:
        emb = get_embedding(enriched)
        interest_embeddings.append(emb)
        print(f"   ✓ vecteur {len(emb)} dimensions généré")

    # ── Étape 3 : Scoring multi-dimensions des articles ──
    print("\n⏳ Scoring des articles...\n")
    print("-" * 65)

    results = []
    for article in ARTICLES:
        article_text = f"titre: {article['title']}\nsujet: {article['topic']}\ncontenu: {article['summary']}"
        article_emb = get_embedding(article_text)

        scores = score_article_multidim(
            article, interest_embeddings, article_emb, user_topics
        )
        results.append({**article, **scores})

    # ── Étape 4 : Affichage résultats ──
    results_sorted = sorted(results, key=lambda x: x["final"], reverse=True)

    print(f"{'Final':<7} {'Sémant':<8} {'Topic':<7} {'Import':<8} {'Label':<20} Titre")
    print("-" * 65)

    SEUIL_HAUT = 0.72
    SEUIL_BAS  = 0.62

    for r in results_sorted:
        f = r["final"]
        if f >= SEUIL_HAUT:
            label = "🟢 très pertinent"
        elif f >= SEUIL_BAS:
            label = "🟡 pertinent"
        else:
            label = "🔴 non pertinent"

        title = r["title"][:30] + "..." if len(r["title"]) > 30 else r["title"]
        print(f"{f:<7} {r['semantic']:<8} {r['topic_match']:<7} {r['importance']:<8} {label:<20} {title}")
        print(f"        Attendu : {r['attendu']}\n")

    # ── Étape 5 : Résumé ──
    print("-" * 65)
    affiches = [r for r in results if r["final"] >= SEUIL_BAS]
    filtres  = [r for r in results if r["final"] < SEUIL_BAS]

    print(f"\n📊 Résumé :")
    print(f"   🟢 Affichés dans le feed : {len(affiches)} / {len(ARTICLES)}")
    print(f"   🔴 Filtrés               : {len(filtres)} / {len(ARTICLES)}")

    print(f"\n✅ Feed utilisateur :")
    for r in sorted(affiches, key=lambda x: x["final"], reverse=True):
        print(f"   {r['final']} — {r['title']}")

    print(f"\n❌ Articles filtrés :")
    for r in sorted(filtres, key=lambda x: x["final"], reverse=True):
        print(f"   {r['final']} — {r['title']}")

    # ── Comparaison V1 vs V2 ──
    print(f"\n{'='*65}")
    print("  COMPARAISON V1 (tags bruts) vs V2 (Groq enrichi + multi-dim)")
    print(f"{'='*65}")
    print(f"{'Article':<45} {'V1 (max)':<10} V2 (final)")
    print("-" * 65)
    v1_scores = [0.661, 0.624, 0.617, 0.616, 0.604, 0.545, 0.535, 0.534]
    for i, r in enumerate(ARTICLES):
        title = r["title"][:42] + "..." if len(r["title"]) > 42 else r["title"]
        v2 = next(x["final"] for x in results if x["id"] == r["id"])
        diff = v2 - v1_scores[i]
        arrow = f"↑ +{diff:.3f}" if diff > 0 else f"↓ {diff:.3f}"
        print(f"{title:<45} {v1_scores[i]:<10} {v2}  {arrow}")


if __name__ == "__main__":
    main()