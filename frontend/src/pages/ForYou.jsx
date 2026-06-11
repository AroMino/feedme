import { useState, useEffect } from "react";
import ArticleCard from "../components/ArticleCard";
import { Sparkles, AlertTriangle, Search } from "lucide-react";

export default function ForYou({ user }) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`http://localhost:5000/api/articles/for-you?user_id=${user.id}`)
      .then((res) => res.json())
      .then((data) => {
        setArticles(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        setError("Failed to load articles.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="page" style={{ textAlign: "center", paddingTop: "8rem" }}>
        <div className="spinner" style={{ margin: "0 auto 1rem" }} />
        <p style={{ color: "var(--text-secondary)" }}>Loading your feed…</p>
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
          <Sparkles className="icon-accent" size={28} /> For You
          <span className="badge badge-accent">{articles.length} articles</span>
        </h1>
        <p className="page-subtitle">
          Selected based on your interests
        </p>
      </div>

      {articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><Search size={48} /></div>
          <h3>No articles found</h3>
          <p>Try adding some interests to your profile to get personalized recommendations.</p>
        </div>
      ) : (
        <div className="articles-grid">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} variant="forYou" />
          ))}
        </div>
      )}
    </div>
  );
}
