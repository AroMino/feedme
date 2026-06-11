import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  LogOut, 
  BookOpen, 
  Hash, 
  Calendar, 
  Trophy, 
  Target, 
  Sparkles, 
  X, 
  Settings, 
  Bell, 
  Moon, 
  Brain 
} from "lucide-react";

export default function Profile({ user: activeUser, onLogout }) {
  const userId = activeUser.id;
  const navigate = useNavigate();
  const [profileData, setProfileData] = useState(null);
  const [interests, setInterests] = useState([]);
  const [newInterest, setNewInterest] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [interestToDelete, setInterestToDelete] = useState(null);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      const [uRes, iRes] = await Promise.all([
        fetch(`http://localhost:5000/api/users/${userId}`),
        fetch(`http://localhost:5000/api/users/${userId}/interests`)
      ]);
      
      const uData = await uRes.json();
      const iData = await iRes.json();
      
      setProfileData(uData);
      setInterests(iData);
    } catch (err) {
      console.error(err);
      setError("Erreur lors du chargement du profil");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
  }, []);

  const handleAddInterest = async (e) => {
    e.preventDefault();
    if (!newInterest.trim()) return;

    try {
      const res = await fetch(`http://localhost:5000/api/users/${userId}/interests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interest_name: newInterest.trim() })
      });
      
      if (res.ok) {
        setNewInterest("");
        fetchUserData(); // Refresh list
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenDeleteModal = (interestName) => {
    setInterestToDelete(interestName);
    setShowDeleteModal(true);
  };

  const handleCloseDeleteModal = () => {
    setShowDeleteModal(false);
    setInterestToDelete(null);
  };

  const handleConfirmDelete = async () => {
    if (!interestToDelete) return;

    try {
      const res = await fetch(`http://localhost:5000/api/users/${userId}/interests/${interestToDelete}`, {
        method: "DELETE"
      });
      
      if (res.ok) {
        handleCloseDeleteModal();
        fetchUserData(); // Refresh list
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogout = () => {
    onLogout();
  };

  if (loading && !profileData) {
    return (
      <div className="page" style={{ textAlign: "center", paddingTop: "8rem" }}>
        <div className="spinner" style={{ margin: "0 auto 1rem" }} />
        <p style={{ color: "var(--text-secondary)" }}>Loading account…</p>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="profile-container">
        {/* Hero Section */}
        <div className="profile-hero" />
        
        <div className="profile-info-header">
          <div className="profile-avatar-large">
            {profileData?.name?.substring(0, 2).toUpperCase() || "AK"}
          </div>
          <div className="profile-info-text">
            <h1 className="profile-name">{profileData?.name}</h1>
            <p className="profile-email">{profileData?.email}</p>
          </div>
          <div className="profile-actions">
            <button onClick={handleLogout} className="btn btn-danger" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <LogOut size={18} /> Logout
            </button>
          </div>
        </div>

        {/* Stats Section */}
        <div className="profile-stats">
          <div className="stat-card">
            <div className="stat-icon-bg"><BookOpen size={20} /></div>
            <span className="stat-value">{profileData?.stats?.articles_read || 0}</span>
            <span className="stat-label">Articles Read</span>
          </div>
          <div className="stat-card">
            <div className="stat-icon-bg"><Hash size={20} /></div>
            <span className="stat-value">{interests.length}</span>
            <span className="stat-label">Interests</span>
          </div>
          <div className="stat-card">
            <div className="stat-icon-bg"><Calendar size={20} /></div>
            <span className="stat-value">{Math.ceil((profileData?.stats?.articles_read || 0) / 2) || 1}</span>
            <span className="stat-label">Active Days</span>
          </div>
          <div className="stat-card">
            <div className="stat-icon-bg"><Trophy size={20} /></div>
            <span className="stat-value">
              {(profileData?.stats?.articles_read || 0) > 10 ? "Top 5%" : "New"}
            </span>
            <span className="stat-label">Status</span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "2rem", alignItems: "start" }}>
          {/* Interests Card */}
          <div className="ai-panel" style={{ margin: 0 }}>
            <div className="ai-panel-header">
              <div className="ai-icon"><Target size={18} /></div>
              <span className="ai-panel-title">Tailored Algorithm</span>
            </div>
            
            <p className="ai-panel-text" style={{ marginBottom: "1.5rem" }}>
              Your feed is curated by cross-referencing these keywords with AI-extracted themes from recent news.
            </p>

            <div className="interests-list" style={{ display: "flex", flexWrap: "wrap", gap: "0.8rem", marginBottom: "1.5rem" }}>
              {interests.map((interest) => (
                <div key={interest.interest_name} className="topic-chip" style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "0.5rem", 
                  padding: "0.5rem 1rem",
                  background: interest.source === 'inferred' ? "rgba(16, 185, 129, 0.05)" : "var(--accent-muted)",
                  border: interest.source === 'inferred' ? "1px solid rgba(16, 185, 129, 0.2)" : "1px solid rgba(99, 102, 241, 0.2)",
                  borderRadius: "12px",
                  color: interest.source === 'inferred' ? "var(--accent-2)" : "var(--accent)",
                  fontWeight: "600",
                  position: "relative"
                }}>
                  {interest.interest_name}
                  {interest.source === 'inferred' && (
                    <Sparkles size={12} style={{ opacity: 0.6, marginLeft: "0.2rem" }} />
                  )}
                  <button 
                    onClick={() => handleOpenDeleteModal(interest.interest_name)}
                    style={{ 
                      background: "none", 
                      border: "none", 
                      color: interest.source === 'inferred' ? "var(--accent-2)" : "var(--accent)", 
                      cursor: "pointer",
                      fontSize: "1.2rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      padding: 0,
                      opacity: 0.7,
                      marginLeft: "0.3rem"
                    }}
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
              {interests.length === 0 && (
                <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No interests defined.</p>
              )}
            </div>

            <form onSubmit={handleAddInterest} style={{ display: "flex", gap: "1rem" }}>
              <input 
                type="text" 
                className="search-input" 
                placeholder="Add a topic..." 
                value={newInterest}
                onChange={(e) => setNewInterest(e.target.value)}
                style={{ flex: 1, borderRadius: "12px" }}
              />
              <button type="submit" className="btn btn-primary" style={{ borderRadius: "12px" }}>
                Add
              </button>
            </form>
          </div>

          {/* Quick Settings Sidebar */}
          <div className="sidebar-static" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div className="ai-panel" style={{ margin: 0, padding: "1.2rem", borderStyle: "solid" }}>
              <span className="sidebar-section-title" style={{ marginBottom: "1rem", fontSize: "0.7rem" }}>Quick Settings</span>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
                <button className="btn btn-secondary" style={{ width: "100%", justifyContent: "flex-start", fontSize: "0.8rem", gap: "0.8rem" }}>
                  <Settings size={16} /> Preferences
                </button>
                <button className="btn btn-secondary" style={{ width: "100%", justifyContent: "flex-start", fontSize: "0.8rem", gap: "0.8rem" }}>
                  <Bell size={16} /> Notifications
                </button>
                <button className="btn btn-secondary" style={{ width: "100%", justifyContent: "flex-start", fontSize: "0.8rem", gap: "0.8rem" }}>
                  <Moon size={16} /> Dark Mode: On
                </button>
              </div>
            </div>
            
            <div className="ai-context-section" style={{ margin: 0 }}>
              <span className="ai-context-title">
                <Brain size={16} style={{ color: "var(--accent)" }} /> IA Insight
              </span>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                Based on your last 5 articles read, you seem to be increasingly interested in <strong>geopolitics</strong>.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Delete Modal */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 className="modal-title">Confirmation</h2>
            <p className="modal-text">
              Are you sure you want to remove "<strong>{interestToDelete}</strong>" from your interests?
              This will impact the relevance of your personalized feed.
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
