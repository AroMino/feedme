import { useNavigate } from "react-router-dom";
import { Newspaper, Zap } from "lucide-react";

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function ArticleCard({ article, variant = "forYou" }) {
  const navigate = useNavigate();
  const score =
    variant === "trending" ? article.trending_score : article.for_you_score;

  return (
    <div
      className="article-card"
      onClick={() => navigate(`/article/${article.id}`)}
    >
      <div className={`article-score-bar ${variant === "trending" ? "trending" : ""}`} />

      {article.image_url ? (
        <img
          className="article-card-image"
          src={article.image_url}
          alt={article.title}
          loading="lazy"
        />
      ) : (
        <div className="article-card-image-placeholder">
          <Newspaper size={40} opacity={0.2} />
        </div>
      )}

      <div className="article-card-body">
        <div className="article-card-meta">
          <span className="article-card-source">{article.author || "News Source"}</span>
          <span className="article-card-date">{formatDate(article.published_at)}</span>
        </div>

        <h3 className="article-card-title">{article.title}</h3>
        <p className="article-card-summary">{article.summary}</p>

        <div className="article-card-footer">
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {article.topics.slice(0, 2).map((t) => (
              <span key={t} className="badge badge-accent">{t}</span>
            ))}
          </div>
          <span className="article-card-score-pill">
            {(score * 100).toFixed(0)}
            &nbsp;
            <Zap size={12} fill="var(--accent)" color="var(--accent)" />
          </span>
        </div>
      </div>
    </div>
  );
}
