import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  ArrowLeft, 
  Search, 
  Brain, 
  Zap, 
  Flame, 
  Award, 
  Globe, 
  ExternalLink, 
  Lightbulb, 
  FileSearch, 
  MessageSquare, 
  X 
} from "lucide-react";

function formatDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function ArticleDetail({ user }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:5000/api/articles/${id}?user_id=${user.id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Article not found");
        return res.json();
      })
      .then((data) => {
        console.log(data)
        setArticle(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        setError(err.message);
        setLoading(false);
      });

    // Record read after 3 seconds
    const timer = setTimeout(() => {
        fetch(`http://localhost:5000/api/users/${user.id}/read/${id}`, { method: "POST" })
            .then(() => console.log("Article read recorded"))
            .catch(err => console.error("Failed to record read:", err));
    }, 3000);

    return () => clearTimeout(timer);
  }, [id, user.id]);

  const handleAiAnalyze = () => {
    setSidebarOpen(true);
    if (!article.ai_analysis) {
       // If not in DB, we could trigger an enrichment here
       // For now, let's just show what we have
    }
    setAiLoading(true);
    setTimeout(() => {
      setAiLoading(false);
    }, 1200);
  };

  if (loading) {
    return (
      <div className="page" style={{ textAlign: "center", paddingTop: "8rem" }}>
        <div className="spinner" style={{ margin: "0 auto 1rem" }} />
        <p style={{ color: "var(--text-secondary)" }}>Loading trending stories…</p>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="detail-page">
        <button className="back-btn" onClick={() => navigate(-1)} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <ArrowLeft size={18} /> Back
        </button>
        <div className="empty-state">
          <div className="empty-state-icon"><Search size={48} /></div>
          <h3>Article not found</h3>
        <p>Try again later while we gather more news.</p>
      </div>
      </div>
    );
  }

  return (
    <div className="detail-page">
      <button className="back-btn" onClick={() => navigate(-1)} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <ArrowLeft size={18} /> Back
      </button>

      {/* Hero Image */}
      {article.image_url && (
        <div className="detail-hero">
          <img src={article.image_url} alt={article.title} />
          <div className="detail-hero-overlay" />
        </div>
      )}

      {/* Meta */}
      <div className="detail-meta">
        <span className="badge badge-accent">{article.source}</span>
        <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          {formatDate(article.published_at)}
        </span>
        {article.author && (
          <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            · {article.author}
          </span>
        )}
      </div>

      <h1 className="detail-title">{article.title}</h1>

      {/* Topics */}
      <div className="detail-topics">
        {article.topics.map((t) => (
          <span key={t} className="topic-chip">
            {t}
          </span>
        ))}
      </div>

      {/* AI Context Section */}
      {article.ai_context && (
        <div className="ai-context-section">
          <div className="ai-context-title">
            <Brain size={20} color="var(--accent)" /> AI Context
          </div>
          <p className="ai-panel-text">{article.ai_context}</p>
        </div>
      )}

      {/* Scores */}
      <div className="detail-scores">
        <div className="score-item">
          <div className="score-icon"><Zap size={16} /></div>
          <span className="score-label">For You</span>
          <span className="score-value">{(article.for_you_score * 100).toFixed(0)}%</span>
        </div>
        <div className="score-item">
          <div className="score-icon" style={{ color: "#f59e0b" }}><Flame size={16} /></div>
          <span className="score-label">Trending</span>
          <span className="score-value" style={{ color: "#f59e0b" }}>
            {(article.trending_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="score-item">
          <div className="score-icon" style={{ color: "var(--accent-2)" }}><Award size={16} /></div>
          <span className="score-label">Quality</span>
          <span className="score-value" style={{ color: "var(--accent-2)" }}>
            {(article.content_quality * 100).toFixed(0)}%
          </span>
        </div>
        <div className="score-item">
          <div className="score-icon" style={{ color: "#c084fc" }}><Globe size={16} /></div>
          <span className="score-label">Relevance</span>
          <span className="score-value" style={{ color: "#c084fc" }}>
            {(article.global_relevance * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-row">
        <button className="btn btn-primary" onClick={handleAiAnalyze} style={{ gap: "0.8rem" }}>
          <Brain size={20} /> AI Analyze
        </button>
        <a
          className="btn btn-secondary"
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ gap: "0.8rem" }}
        >
          <ExternalLink size={20} /> Read Full Article
        </a>
      </div>

      {/* Summary box */}
      <div className="detail-summary-box">{article.summary}</div>

      {/* Full content */}
      <p className="detail-content">{article.content}</p>

      {/* Sidebar Overlay */}
      <div 
        className={`sidebar-overlay ${sidebarOpen ? 'active' : ''}`} 
        onClick={() => setSidebarOpen(false)} 
      />

      {/* AI Analysis Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'active' : ''}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-section-title" style={{ fontSize: '1rem', display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <Brain size={18} color="var(--accent)" /> IA Deep Analysis
          </h2>
          <button className="sidebar-close" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>

        {aiLoading ? (
          <div className="ai-loading" style={{ marginTop: '2rem' }}>
            <div className="spinner" />
            L'IA approfondit son analyse…
          </div>
        ) : (
          <>
            <div className="sidebar-section" style={{ marginTop: '1rem' }}>
              <span className="sidebar-section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Lightbulb size={16} /> Explanation
              </span>
              <p className="sidebar-section-text">{article.ai_context}</p>
            </div>

            <div className="sidebar-section">
              <span className="sidebar-section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <FileSearch size={16} /> Detailed Analysis
              </span>
              <p className="sidebar-section-text">{article.ai_analysis}</p>
            </div>

            <div className="sidebar-section">
              <span className="sidebar-section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <MessageSquare size={16} /> AI Commentary
              </span>
              <p className="sidebar-section-text">{article.ai_commentary}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
