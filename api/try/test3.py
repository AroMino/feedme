"""
Test matching V2b — Sans appel LLM pour l'enrichissement
(enrichissements pré-écrits pour économiser le quota)
"""

import os
import time
import numpy as np
from google import genai
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_EMBED = "gemini-embedding-001"

# ─── PROFIL ENRICHI (simulé sans LLM) ────────────────────
ENRICHED_INTERESTS = [
    {
        "raw": "intelligence artificielle",
        "enriched": """Intelligence artificielle, machine learning, deep learning,
        réseaux de neurones, LLM, GPT, NLP, computer vision, IA générative,
        modèles de langage, ChatGPT, automatisation intelligente, algorithmes
        d apprentissage, traitement du langage naturel, OpenAI, Google AI."""
    },
    {
        "raw": "startups",
        "enriched": """Startup, entrepreneuriat, levée de fonds, capital-risque,
        venture capital, scale-up, licorne, financement, incubateur, accélérateur,
        fondateur, pivot, MVP, product market fit, croissance, disruption,
        innovation, jeune entreprise, tech startup, seed funding."""
    },
    {
        "raw": "innovation technologique",
        "enriched": """Innovation technologique, nouvelles technologies, tech,
        disruption numérique, transformation digitale, R&D, recherche développement,
        breakthrough technologique, avancée scientifique, révolution numérique,
        technologies émergentes, futurisme tech, progrès technologique."""
    }
]

USER_TOPICS = ["technologie", "business"]

# ─── ARTICLES ─────────────────────────────────────────────
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
    time.sleep(0.3)
    result = client.models.embed_content(
        model=MODEL_EMBED,
        contents=text
    )
    return np.array(result.embeddings[0].values)


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(np.dot(v1, v2) / norm) if norm else 0.0


def score_article(article_emb, interest_embs, article, user_topics):
    semantic  = max(cosine_similarity(article_emb, ie) for ie in interest_embs)
    topic     = 1.0 if article["topic"] in user_topics else 0.0
    importance = article["importance"] / 10.0
    final = (semantic * 0.65) + (topic * 0.20) + (importance * 0.15)
    return {
        "semantic":   round(semantic, 3),
        "topic":      round(topic, 3),
        "importance": round(importance, 3),
        "final":      round(final, 3)
    }


# ─── MAIN ─────────────────────────────────────────────────

def main():
    print("=" * 68)
    print("  TEST MATCHING SÉMANTIQUE V2 — ENRICHI (sans quota LLM)")
    print("=" * 68)

    # Étape 1 — Embeddings profil enrichi
    print("\n👤 Profil utilisateur enrichi :\n")
    interest_embs = []
    for item in ENRICHED_INTERESTS:
        print(f"   '{item['raw']}'")
        print(f"   → {item['enriched'][:80].strip()}...")
        emb = get_embedding(item["enriched"])
        interest_embs.append(emb)
        print(f"   ✓ vecteur {len(emb)} dims\n")

    # Étape 2 — Scoring articles
    print("⏳ Scoring des articles...\n")

    results = []
    for article in ARTICLES:
        text = f"titre: {article['title']}\nsujet: {article['topic']}\ncontenu: {article['summary']}"
        emb  = get_embedding(text)
        scores = score_article(emb, interest_embs, article, USER_TOPICS)
        results.append({**article, **scores})

    # Étape 3 — Affichage
    results_sorted = sorted(results, key=lambda x: x["final"], reverse=True)

    SEUIL_HAUT = 0.72
    SEUIL_BAS  = 0.62

    print(f"{'Final':<7} {'Séman':<7} {'Topic':<7} {'Imprt':<7} {'Label':<20} Titre")
    print("-" * 68)

    for r in results_sorted:
        f = r["final"]
        if f >= SEUIL_HAUT:
            label = "🟢 très pertinent"
        elif f >= SEUIL_BAS:
            label = "🟡 pertinent"
        else:
            label = "🔴 non pertinent"
        title = r["title"][:28] + "..." if len(r["title"]) > 28 else r["title"]
        print(f"{f:<7} {r['semantic']:<7} {r['topic']:<7} {r['importance']:<7} {label:<20} {title}")
        print(f"        Attendu : {r['attendu']}\n")

    # Résumé
    print("-" * 68)
    affiches = [r for r in results if r["final"] >= SEUIL_BAS]
    filtres  = [r for r in results if r["final"] < SEUIL_BAS]

    print(f"\n📊 Résumé : {len(affiches)} affichés / {len(filtres)} filtrés\n")

    print("✅ Feed utilisateur :")
    for r in sorted(affiches, key=lambda x: x["final"], reverse=True):
        print(f"   {r['final']} — {r['title']}")

    print("\n❌ Articles filtrés :")
    for r in sorted(filtres, key=lambda x: x["final"], reverse=True):
        print(f"   {r['final']} — {r['title']}")

    # Comparaison V1 vs V2
    V1 = {1:0.616, 2:0.624, 3:0.617, 4:0.661, 5:0.534, 6:0.535, 7:0.545, 8:0.604}
    print(f"\n{'='*68}")
    print("  COMPARAISON V1 vs V2")
    print(f"{'='*68}")
    print(f"{'Titre':<42} {'V1':<8} {'V2':<8} Diff")
    print("-" * 68)
    for r in results_sorted:
        v1 = V1[r["id"]]
        v2 = r["final"]
        diff = v2 - v1
        arrow = f"↑ +{diff:.3f}" if diff > 0 else f"↓ {diff:.3f}"
        title = r["title"][:40] + ".." if len(r["title"]) > 40 else r["title"]
        print(f"{title:<42} {v1:<8} {v2:<8} {arrow}")

if __name__ == "__main__":
    main()