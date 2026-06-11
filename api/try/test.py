import os
import numpy as np
from google import genai
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# ─── DONNÉES DE TEST ──────────────────────────────────────

USER_INTERESTS = [
    "intelligence artificielle",
    "startups",
    "innovation technologique"
]

ARTICLES = [
    {
        "id": 1,
        "title": "Google dévoile Gemini Ultra 3.0, un bond en avant pour le machine learning",
        "tags": "machine learning deep learning neural networks Google LLM",
        "attendu": "✅ très pertinent"
    },
    {
        "id": 2,
        "title": "ChatGPT dépasse 500 millions d'utilisateurs actifs",
        "tags": "ChatGPT OpenAI LLM intelligence artificielle générative",
        "attendu": "✅ très pertinent"
    },
    {
        "id": 3,
        "title": "Une jeune startup lève 10M€ pour révolutionner la logistique",
        "tags": "startup levée de fonds financement entrepreneuriat logistique",
        "attendu": "✅ pertinent"
    },
    {
        "id": 4,
        "title": "Tesla autopilot : l'IA redéfinit la conduite autonome",
        "tags": "Tesla conduite autonome voiture électrique autopilot IA",
        "attendu": "✅ pertinent"
    },
    {
        "id": 5,
        "title": "Les Jeux Olympiques 2028 : Los Angeles se prépare",
        "tags": "sport JO olympique Los Angeles athlétisme",
        "attendu": "❌ non pertinent"
    },
    {
        "id": 6,
        "title": "Recette : tarte tatin aux pommes caramélisées",
        "tags": "cuisine recette dessert pommes caramel",
        "attendu": "❌ non pertinent"
    },
    {
        "id": 7,
        "title": "Élections européennes : les enjeux économiques en 2026",
        "tags": "politique élections Europe économie parlement",
        "attendu": "❌ non pertinent"
    },
    {
        "id": 8,
        "title": "Nvidia annonce une puce révolutionnaire pour les data centers IA",
        "tags": "Nvidia GPU chip data center calcul haute performance IA",
        "attendu": "✅ très pertinent"
    },
]

# ─── FONCTIONS ────────────────────────────────────────────

def get_embedding(text: str) -> np.ndarray:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return np.array(result.embeddings[0].values)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    dot = np.dot(vec1, vec2)
    norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return float(dot / norm) if norm else 0.0


def score_article(article_emb: np.ndarray, interest_embs: list) -> float:
    return max(cosine_similarity(article_emb, ie) for ie in interest_embs)


# ─── MAIN ─────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  TEST MATCHING SÉMANTIQUE — EMBEDDINGS")
    print("=" * 65)
    print(f"\n👤 Centres d'intérêt : {', '.join(USER_INTERESTS)}\n")
    print("⏳ Génération embeddings utilisateur...")

    interest_embs = []
    for interest in USER_INTERESTS:
        emb = get_embedding(interest)
        interest_embs.append(emb)
        print(f"   ✓ '{interest}' → vecteur {len(emb)} dims")

    print("\n⏳ Scoring des articles...\n")
    print("-" * 65)

    results = []
    for article in ARTICLES:
        text = f"{article['title']} {article['tags']}"
        emb = get_embedding(text)
        score = score_article(emb, interest_embs)
        results.append({**article, "score": score})

    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)

    print(f"{'Score':<8} {'Label':<22} Titre")
    print("-" * 65)

    for r in results_sorted:
        s = r["score"]
        if s >= 0.75:
            label = "🟢 très pertinent"
        elif s >= 0.60:
            label = "🟡 pertinent"
        else:
            label = "🔴 non pertinent"

        title = r["title"][:42] + "..." if len(r["title"]) > 42 else r["title"]
        print(f"{s:.3f}   {label:<22} {title}")
        print(f"         Attendu : {r['attendu']}\n")

    print("-" * 65)
    affiches = [r for r in results if r["score"] >= 0.60]
    filtres  = [r for r in results if r["score"] < 0.60]

    print(f"\n📊 Résumé sur {len(ARTICLES)} articles du jour :")
    print(f"   🟢 Affichés dans le feed : {len(affiches)}")
    print(f"   🔴 Filtrés               : {len(filtres)}")

    print(f"\n✅ Feed de l'utilisateur :")
    for r in sorted(affiches, key=lambda x: x["score"], reverse=True):
        print(f"   {r['score']:.3f} — {r['title']}")

    print(f"\n❌ Articles ignorés :")
    for r in sorted(filtres, key=lambda x: x["score"], reverse=True):
        print(f"   {r['score']:.3f} — {r['title']}")

if __name__ == "__main__":
    main()