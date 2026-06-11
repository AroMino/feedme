import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:5000/api/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        onLogin(data);
        navigate("/");
      } else {
        setError(data.error || "Login failed");
      }
    } catch (err) {
      console.error(err);
      setError("Server error. Make sure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page" style={{ 
      display: "flex", 
      alignItems: "center", 
      justifyContent: "center", 
      minHeight: "80vh" 
    }}>
      <div className="ai-panel" style={{ width: "100%", maxWidth: "400px", padding: "2.5rem" }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>📰</div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: "700", marginBottom: "0.5rem" }}>Welcome to FeedMe</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>Sign in to see your personalized feed</p>
        </div>

        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-muted)" }}>Email Address</label>
            <input 
              type="email" 
              className="search-input" 
              placeholder="alice@example.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ width: "100%" }}
            />
          </div>

          {error && <p style={{ color: "#ef4444", fontSize: "0.85rem", textAlign: "center" }}>{error}</p>}

          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={loading}
            style={{ width: "100%", justifyContent: "center", padding: "0.8rem" }}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <div style={{ marginTop: "2rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.8rem", textAlign: "center" }}>
            Test accounts:
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", justifyContent: "center" }}>
            <button className="badge badge-accent" onClick={() => setEmail("alice@example.com")} style={{ cursor: "pointer", border: "none" }}>
              alice@example.com
            </button>
            <button className="badge badge-accent" onClick={() => setEmail("bob@example.com")} style={{ cursor: "pointer", border: "none" }}>
              bob@example.com
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
