"""
Test matching sémantique V3 — Optimisations précision :
1. Sémantique : max + moyenne pondérée (anti faux-positifs)
2. Topic match sémantique graduel (exit du binaire 0/1)
3. Poids rééquilibrés : sémantique 0.75 / topic 0.20 / importance 0.05
4. Seuils dynamiques basés sur la distribution des scores
5. Embedding article : titre + résumé séparés et combinés
"""

import os
import time
import numpy as np
from google import genai
from groq import Groq

from dotenv import load_dotenv
load_dotenv()

# ─── CLIENTS ──────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client   = Groq(api_key=GROQ_API_KEY)

MODEL_EMBED = "gemini-embedding-001"
GROQ_MODEL  = "llama-3.1-8b-instant"

# ─── PROFIL UTILISATEUR ───────────────────────────────────

USER_INTERESTS_RAW = [
    "intelligence artificielle",
    "startups",
    "innovation technologique"
]

# ─── ARTICLES SIMULÉS ─────────────────────────────────────

ARTICLES = [
    {
        "id": 1,
        "title": "Google dévoile Gemini Ultra 3.0",
        "topic": "technologie",
        "summary": "Google présente son nouveau modèle de langage Gemini Ultra 3.0 basé sur le deep learning et les réseaux de neurones transformers, surpassant GPT-4 sur les benchmarks IA. Ce LLM représente une avancée majeure pour l intelligence artificielle générative.",
        "importance": 9.0,
        "attendu": "✅ très pertinent"
    },
    {
        "id": 2,
        "title": "ChatGPT dépasse 500 millions d'utilisateurs",
        "topic": "technologie",
        "summary": "OpenAI annonce que ChatGPT, son assistant basé sur les LLM et l intelligence artificielle générative, franchit le cap des 500 millions d utilisateurs actifs mondiaux. Une adoption massive de l IA dans le grand public.",
        "importance": 8.5,
        "attendu": "✅ très pertinent"
    },
    {
        "id": 3,
        "title": "Une startup lève 10M€ pour révolutionner la logistique",
        "topic": "business",
        "summary": "Une jeune startup française fondée en 2024 lève 10 millions d euros auprès de fonds de capital-risque pour développer sa solution d optimisation logistique. L entrepreneuriat tech européen continue de croître.",
        "importance": 6.0,
        "attendu": "✅ pertinent"
    },
    {
        "id": 4,
        "title": "Tesla autopilot : l'IA redéfinit la conduite autonome",
        "topic": "technologie",
        "summary": "Tesla améliore son système autopilot grâce à de nouveaux algorithmes d intelligence artificielle et de vision par ordinateur. La conduite autonome de niveau 4 se rapproche grâce aux avancées en machine learning.",
        "importance": 7.5,
        "attendu": "✅ pertinent"
    },
    {
        "id": 5,
        "title": "Les Jeux Olympiques 2028 : Los Angeles se prépare",
        "topic": "sport",
        "summary": "Los Angeles avance dans la préparation des Jeux Olympiques de 2028. Les infrastructures sportives et les plans de transport sont en cours de finalisation pour accueillir les athlètes du monde entier.",
        "importance": 5.0,
        "attendu": "❌ non pertinent"
    },
    {
        "id": 6,
        "title": "Recette : tarte tatin aux pommes caramélisées",
        "topic": "cuisine",
        "summary": "Découvrez la recette traditionnelle de la tarte tatin aux pommes caramélisées. Une pâte feuilletée croustillante, des pommes dorées au beurre et au sucre, pour un dessert savoureux et facile à réaliser.",
        "importance": 2.0,
        "attendu": "❌ non pertinent"
    },
    {
        "id": 7,
        "title": "Élections européennes : les enjeux économiques",
        "topic": "politique",
        "summary": "Les prochaines élections européennes cristallisent les débats autour des politiques économiques, de la fiscalité des entreprises et de la souveraineté industrielle de l Union Européenne face aux États-Unis et la Chine.",
        "importance": 7.0,
        "attendu": "❌ non pertinent"
    },
    {
        "id": 8,
        "title": "Nvidia annonce une puce révolutionnaire pour l'IA",
        "topic": "technologie",
        "summary": "Nvidia présente son nouveau GPU H300 spécialement conçu pour l entraînement de modèles d intelligence artificielle en data center. Cette puce offre des performances 4x supérieures pour le deep learning et les LLM.",
        "importance": 9.0,
        "attendu": "✅ très pertinent"
    },
]

# ─── FONCTIONS ────────────────────────────────────────────

def get_embedding(text: str) -> np.ndarray:
    """Embedding via Gemini"""
    time.sleep(0.5)
    result = gemini_client.models.embed_content(
        model=MODEL_EMBED,
        contents=text
    )
    return np.array(result.embeddings[0].values)


def get_article_embedding(article: dict) -> np.ndarray:
    """Optim. #5 — Titre + résumé embeddings séparés, combinés avec pondération"""
    emb_title   = get_embedding(article["title"])
    emb_summary = get_embedding(article["summary"])
    combined = (emb_title * 0.4) + (emb_summary * 0.6)
    norm = np.linalg.norm(combined)
    return combined / norm if norm else combined


def generate_user_topics(interests: list) -> list:
    """Génère une liste de topics/domaines génériques à partir des interests via Groq"""
    interests_str = ", ".join(interests)
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un classificateur de domaines thématiques. "
                    "Tu réponds UNIQUEMENT par une liste de mots séparés par des virgules. "
                    "Aucune phrase, aucune explication."
                )
            },
            {
                "role": "user",
                "content": (
                    f"À partir de ces centres d'intérêt : {interests_str}\n"
                    f"Génère 5 à 8 domaines/topics génériques associés parmi des labels courts "
                    f"comme : technologie, business, science, politique, sport, santé, finance, "
                    f"environnement, culture, éducation, entrepreneuriat, informatique.\n"
                    f"Format : topic1, topic2, topic3, ..."
                )
            }
        ],
        max_tokens=100,
        temperature=0.2
    )
    raw = response.choices[0].message.content.strip()
    return [t.strip().lower() for t in raw.split(",") if t.strip()]


def enrich_interest_with_llm(interest: str) -> str:
    """Enrichissement via Groq — liste dense de mots-clés"""
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un générateur de mots-clés. "
                    "Tu réponds UNIQUEMENT par une liste de mots-clés et termes séparés par des virgules. "
                    "Aucune phrase, aucune explication, aucune introduction. Seulement des mots-clés."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Donne 15 à 20 mots-clés, synonymes et termes associés pour : \"{interest}\".\n"
                    f"Format attendu : terme1, terme2, terme3, ..."
                )
            }
        ],
        max_tokens=200,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(np.dot(v1, v2) / norm) if norm else 0.0


def score_article_multidim(article: dict,
                            interest_embeddings: list,
                            article_embedding: np.ndarray,
                            topic_embeddings: list) -> dict:
    """Score multi-dimensions — version optimisée"""

    # Dimension 1 — Optim. #1 : max + moyenne pondérée (anti faux-positifs)
    scores = [cosine_similarity(article_embedding, ie) for ie in interest_embeddings]
    semantic = (max(scores) * 0.7) + (float(np.mean(scores)) * 0.3)

    # Dimension 2 — Optim. #2 : topic match sémantique graduel (exit du binaire)
    topic_scores = [
        cosine_similarity(te, ie)
        for te in topic_embeddings
        for ie in interest_embeddings
    ]
    topic_match = max(topic_scores) if topic_scores else 0.0

    # Dimension 3 — Importance (poids réduit, optim. #3)
    importance = article["importance"] / 10.0

    # Score final — Optim. #3 : poids rééquilibrés
    final = (semantic * 0.75) + (topic_match * 0.20) + (importance * 0.05)

    return {
        "semantic":    round(semantic, 3),
        "topic_match": round(topic_match, 3),
        "importance":  round(importance, 3),
        "final":       round(final, 3)
    }


# ─── MAIN ─────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  TEST MATCHING SÉMANTIQUE V3 — PRÉCISION OPTIMISÉE")
    print("=" * 65)

    # ── Étape 1 : Enrichissement via Groq ──
    print(f"\n👤 Centres d'intérêt bruts : {', '.join(USER_INTERESTS_RAW)}")
    print(f"\n🧠 Enrichissement via Groq ({GROQ_MODEL})...\n")

    enriched_interests = []
    for interest in USER_INTERESTS_RAW:
        enriched = enrich_interest_with_llm(interest)
        enriched_interests.append(enriched)
        print(f"   '{interest}'\n   → {enriched[:120]}...\n")

    # ── Topics générés par LLM ──
    print("🏷️  Génération des topics utilisateur via Groq...")
    user_topics = generate_user_topics(USER_INTERESTS_RAW)
    print(f"   → Topics détectés : {user_topics}\n")

    # ── Étape 2 : Embeddings profil ──
    print("⏳ Génération embeddings profil (Gemini)...")
    interest_embeddings = []
    for enriched in enriched_interests:
        emb = get_embedding(enriched)
        interest_embeddings.append(emb)
        print(f"   ✓ vecteur {len(emb)} dimensions généré")

    # ── Étape 3 : Embeddings topics utilisateur ──
    print("\n⏳ Génération embeddings topics utilisateur...")
    topic_embeddings = []
    for topic in user_topics:
        emb = get_embedding(topic)
        topic_embeddings.append(emb)
    print(f"   ✓ {len(topic_embeddings)} topics embarqués")

    # ── Étape 4 : Scoring articles ──
    print("\n⏳ Scoring des articles (titre + résumé séparés)...\n")
    print("-" * 65)

    results = []
    for article in ARTICLES:
        # Optim. #5 : embedding combiné titre/résumé
        article_emb = get_article_embedding(article)

        scores = score_article_multidim(
            article, interest_embeddings, article_emb, topic_embeddings
        )
        results.append({**article, **scores})

    # ── Étape 5 : Seuils dynamiques (optim. #4) ──
    all_scores = [r["final"] for r in results]
    mean_s = float(np.mean(all_scores))
    std_s  = float(np.std(all_scores))
    SEUIL_HAUT = round(mean_s + 0.5 * std_s, 3)
    SEUIL_BAS  = round(mean_s - 0.2 * std_s, 3)
    print(f"📐 Seuils dynamiques — μ={mean_s:.3f} σ={std_s:.3f}")
    print(f"   🟢 Très pertinent : >= {SEUIL_HAUT}")
    print(f"   🟡 Pertinent      : >= {SEUIL_BAS}")
    print(f"   🔴 Filtré         :  < {SEUIL_BAS}\n")

    # ── Étape 6 : Affichage résultats ──
    results_sorted = sorted(results, key=lambda x: x["final"], reverse=True)

    print(f"{'Final':<7} {'Sémant':<8} {'Topic':<7} {'Import':<8} {'Label':<20} Titre")
    print("-" * 65)

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

    # ── Résumé ──
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

    # ── Comparaison V1 vs V2 vs V3 ──
    print(f"\n{'='*65}")
    print("  COMPARAISON V1 → V2 → V3")
    print(f"{'='*65}")
    print(f"{'Article':<40} {'V1':<8} {'V2':<8} V3")
    print("-" * 65)
    v1_scores = [0.661, 0.624, 0.617, 0.616, 0.604, 0.545, 0.535, 0.534]
    v2_scores = [0.720, 0.690, 0.650, 0.670, 0.610, 0.520, 0.540, 0.730]  # référence approximative
    for i, r in enumerate(ARTICLES):
        title = r["title"][:37] + "..." if len(r["title"]) > 37 else r["title"]
        v3 = next(x["final"] for x in results if x["id"] == r["id"])
        diff = v3 - v1_scores[i]
        arrow = f"↑ +{diff:.3f}" if diff > 0 else f"↓ {diff:.3f}"
        print(f"{title:<40} {v1_scores[i]:<8} {v2_scores[i]:<8} {v3}  {arrow}")


if __name__ == "__main__":
    main()