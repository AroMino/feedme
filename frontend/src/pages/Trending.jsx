import { useState, useEffect } from "react";
import ArticleCard from "../components/ArticleCard";
import { Flame, AlertTriangle, TrendingUp } from "lucide-react";

export default function Trending() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user") || '{"id": 1}');
    setLoading(true);
    fetch(`http://localhost:5000/api/articles/trending?user_id=${user.id}`)
      .then((res) => res.json())
      .then((data) => {
        setArticles(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        setError("Failed to load trending articles.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="page" style={{ textAlign: "center", paddingTop: "8rem" }}>
        <div className="spinner" style={{ margin: "0 auto 1rem" }} />
        <p style={{ color: "var(--text-secondary)" }}>Loading global trends…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page" style={{ textAlign: "center", paddingTop: "8rem" }}>
        <div className="empty-state-icon"><AlertTriangle size={48} /></div>
        <p style={{ color: "var(--text-secondary)" }}>{error}</p>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title" style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
          <Flame className="icon-trending" size={28} /> Trending
          <span className="badge badge-warm">{articles.length} articles</span>
        </h1>
        <p className="page-subtitle">
          The most popular stories right now
        </p>
      </div>

      {articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><TrendingUp size={48} /></div>
          <p>No trending articles at the moment.</p>
        </div>
      ) : (
        <div className="articles-grid">
          {articles.map((article, i) => (
            <div key={article.id} style={{ position: "relative" }}>
              {i < 3 && (
                <span
                  style={{
                    position: "absolute",
                    top: "12px",
                    right: "16px",
                    zIndex: 1,
                    fontSize: "1.1rem",
                    lineHeight: 1,
                  }}
                >
                  {["🥇", "🥈", "🥉"][i]}
                </span>
              )}
              <ArticleCard article={article} variant="trending" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
