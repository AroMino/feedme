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
  X,
  Target,
  Plus,
  Check
} from "lucide-react";

function formatDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

import { useToast } from "../context/ToastContext";

export default function ArticleDetail({ user }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [article, setArticle] = useState(null);
  const [userInterests, setUserInterests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [followLoading, setFollowLoading] = useState(null);

  const fetchUserInterests = async () => {
    try {
      const res = await fetch(`http://localhost:5000/api/users/${user.id}/interests`);
      const data = await res.json();
      setUserInterests(data.map(i => i.interest_name));
    } catch (err) {
      console.error("Failed to fetch interests", err);
    }
  };

  useEffect(() => {
    setLoading(true);
    
    Promise.all([
      fetch(`http://localhost:5000/api/articles/${id}?user_id=${user.id}`).then(res => {
        if (!res.ok) throw new Error("Article not found");
        return res.json();
      }),
      fetchUserInterests()
    ])
    .then(([artData]) => {
      setArticle(artData);
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

  const handleAiAnalyze = async () => {
    setSidebarOpen(true);
    
    // If we already have analysis from a previous session or other user, don't re-run
    if (article.ai_analysis) return;

    setAiLoading(true);
    try {
      const res = await fetch(`http://localhost:5000/api/articles/${id}/analyze`, { method: "POST" });
      const data = await res.json();
      
      if (res.ok) {
        setArticle(prev => ({
          ...prev,
          ...data
        }));
      } else {
        console.error("Analysis failed:", data.error);
        addToast(data.error || "Analysis failed. Please try again later.", "error");
        // Don't keep sidebar open if it failed and we have no data
        if (!article.ai_analysis) setSidebarOpen(false);
      }
    } catch (err) {
      console.error("Analysis error:", err);
      addToast("Connection error. Is the server running?", "error");
      setSidebarOpen(false);
    } finally {
      setAiLoading(false);
    }
  };

  const handleFollowTopic = async (topicName) => {
    setFollowLoading(topicName);
    try {
      const res = await fetch(`http://localhost:5000/api/users/${user.id}/interests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          interest_name: topicName,
          source: 'suggested'
        })
      });
      if (res.ok) {
        await fetchUserInterests();
        addToast(`Now following ${topicName}`, "success");
      } else {
        addToast("Failed to follow topic", "error");
      }
    } catch (err) {
      console.error("Failed to follow topic", err);
      addToast("Network error while following topic", "error");
    } finally {
      setFollowLoading(null);
    }
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
        {article?.topics?.map((t) => (
          <span key={t} className="topic-chip">
            {t}
          </span>
        ))}
      </div>

      {/* AI Context Section */}
      {/* {article.ai_explanation && (
        <div className="ai-context-section">
          <div className="ai-context-title">
            <Brain size={20} color="var(--accent)" /> AI Context
          </div>
          <p className="ai-panel-text">{article.ai_explanation}</p>
        </div>
      )} */}

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

      {/* Refine Feed Section */}
      {article?.suggested_topics?.length > 0 && (
        <div className="refine-feed-card">
          <div className="refine-feed-header">
            <div className="refine-icon"><Target size={20} /></div>
            <div className="refine-text">
              <h4>Refine Your Feed</h4>
              <p>Follow these broad categories to see more content like this.</p>
            </div>
          </div>
          <div className="refine-topics">
            {article?.suggested_topics?.map(t => {
                const isFollowed = userInterests.includes(t);
                return (
                    <button 
                        key={t} 
                        className={`follow-chip ${isFollowed ? 'followed' : ''}`}
                        onClick={() => !isFollowed && handleFollowTopic(t)}
                        disabled={isFollowed || followLoading === t}
                    >
                        {isFollowed ? <Check size={14} /> : <Plus size={14} />}
                        {t}
                    </button>
                );
            })}
          </div>
        </div>
      )}

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
            <p>L'IA approfondit son analyse…</p>
          </div>
        ) : (
          <div className="sidebar-content animate">
            <div className="sidebar-section" style={{ marginTop: '1rem' }}>
              <span className="sidebar-section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Lightbulb size={16} /> Explanation
              </span>
              <p className="sidebar-section-text" style={{ whiteSpace: 'pre-wrap' }}>
                {typeof article?.ai_explanation === 'object' 
                  ? JSON.stringify(article.ai_explanation, null, 2) 
                  : (article?.ai_explanation || "Analysis pending...")}
              </p>
            </div>

            <div className="sidebar-section">
              <span className="sidebar-section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <FileSearch size={16} /> Detailed Analysis
              </span>
              <p className="sidebar-section-text" style={{ whiteSpace: 'pre-wrap' }}>
                {typeof article?.ai_analysis === 'object' 
                  ? JSON.stringify(article.ai_analysis, null, 2) 
                  : (article?.ai_analysis || "No deep analysis available.")}
              </p>
            </div>

            <div className="sidebar-section">
              <span className="sidebar-section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <MessageSquare size={16} /> AI Commentary
              </span>
              <p className="sidebar-section-text" style={{ whiteSpace: 'pre-wrap' }}>
                {typeof article?.ai_commentary === 'object' 
                  ? JSON.stringify(article.ai_commentary, null, 2) 
                  : (article?.ai_commentary || "No commentary available yet.")}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
