import { useState, useEffect } from "react";
import { Plus, Trash2, Globe, AlertCircle, CheckCircle2 } from "lucide-react";

export default function RSSSourceManager() {
  const [sources, setSources] = useState([]);
  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [sourceToDelete, setSourceToDelete] = useState(null);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://localhost:5000/api/sources");
      const data = await res.json();
      setSources(data);
    } catch (err) {
      console.error(err);
      setError("Failed to load sources");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newName.trim() || !newUrl.trim()) return;

    try {
      setError(null);
      setSuccess(null);
      const res = await fetch("http://localhost:5000/api/sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName.trim(), url: newUrl.trim() })
      });
      
      if (res.ok) {
        setNewName("");
        setNewUrl("");
        setSuccess("Source added successfully!");
        fetchSources();
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const data = await res.json();
        setError(data.error || "Failed to add source");
      }
    } catch (err) {
      setError("Network error");
    }
  };

  const handleOpenDeleteModal = (id, name) => {
    setSourceToDelete({ id, name });
    setShowDeleteModal(true);
  };

  const handleCloseDeleteModal = () => {
    setShowDeleteModal(false);
    setSourceToDelete(null);
  };

  const handleConfirmDelete = async () => {
    if (!sourceToDelete) return;
    
    try {
      const res = await fetch(`http://localhost:5000/api/sources/${sourceToDelete.id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        handleCloseDeleteModal();
        fetchSources();
      }
    } catch (err) {
      setError("Failed to delete source");
    }
  };

  return (
    <div className="ai-panel" style={{ margin: "2rem 0" }}>
      <div className="ai-panel-header">
        <div className="ai-icon"><Globe size={18} /></div>
        <span className="ai-panel-title">Inspiration Sources (RSS)</span>
      </div>

      <p className="ai-panel-text" style={{ marginBottom: "1.5rem" }}>
        Manage the news feeds that FeedMe monitors to discover new articles.
      </p>

      {error && (
        <div className="toast error" style={{ position: "static", marginBottom: "1rem", width: "100%", transform: "none" }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {success && (
        <div className="toast success" style={{ position: "static", marginBottom: "1rem", width: "100%", transform: "none", background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)", color: "var(--accent-2)" }}>
          <CheckCircle2 size={18} /> {success}
        </div>
      )}

      <div className="sources-list" style={{ display: "flex", flexDirection: "column", gap: "0.8rem", marginBottom: "2rem" }}>
        {sources.map((source) => (
          <div key={source.id} style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            alignItems: "center", 
            padding: "1rem", 
            background: "rgba(255,255,255,0.03)", 
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.05)"
          }}>
            <div>
              <div style={{ fontWeight: "600", fontSize: "0.95rem" }}>{source.name}</div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>{source.url}</div>
            </div>
            <button 
              onClick={() => handleOpenDeleteModal(source.id, source.name)}
              className="btn-icon" 
              style={{ color: "#ef4444", opacity: 0.6 }}
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
        {sources.length === 0 && !loading && (
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", py: "1rem" }}>
            No RSS sources configured.
          </p>
        )}
      </div>

      <form onSubmit={handleAdd} style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: "1rem" }}>
        <input 
          type="text" 
          className="search-input" 
          placeholder="Source Name (e.g. BBC)" 
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          style={{ borderRadius: "12px", fontSize: "0.9rem" }}
        />
        <input 
          type="text" 
          className="search-input" 
          placeholder="RSS URL" 
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          style={{ borderRadius: "12px", fontSize: "0.9rem" }}
        />
        <button type="submit" className="btn btn-primary" style={{ borderRadius: "12px", width: "45px", height: "45px", padding: 0, justifyContent: "center" }}>
          <Plus size={20} />
        </button>
      </form>

      {/* Custom Delete Modal */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 className="modal-title">Confirmation</h2>
            <p className="modal-text">
              Are you sure you want to delete source "<strong>{sourceToDelete?.name}</strong>"?
              FeedMe will no longer monitor this RSS feed for new articles.
            </p>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={handleCloseDeleteModal}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleConfirmDelete} style={{ background: '#ef4444', color: '#fff' }}>
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
