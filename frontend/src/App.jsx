import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import ForYou from "./pages/ForYou";
import Trending from "./pages/Trending";
import ArticleDetail from "./pages/ArticleDetail";
import Profile from "./pages/Profile";
import Login from "./pages/Login";

import ToastContainer from "./components/ToastContainer";
import { useToast } from "./context/ToastContext";

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncVersion, setSyncVersion] = useState(0);
  const { addToast } = useToast();

  const syncUserFeed = async (userId) => {
    try {
      setSyncing(true);
      const res = await fetch(`http://localhost:5000/api/users/${userId}/sync`, { method: "POST" });
      if (!res.ok) throw new Error("Sync failed");
      setSyncVersion(prev => prev + 1);
    } catch (err) {
      console.error("Failed to sync feed:", err);
      addToast("Failed to refresh your feed. Check your connection.", "error");
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser && !user) {
      const u = JSON.parse(savedUser);
      setUser(u);
      syncUserFeed(u.id);
    }
    setLoading(false);
  }, [user]);

  const handleLogin = async (userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
    await syncUserFeed(userData.id);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  if (loading) return null;

  return (
    <BrowserRouter>
      {user && <Navbar user={user} onLogout={handleLogout} />}
      {syncing && (
        <div style={{
          position: "fixed", top: 0, left: 0, width: "100%", height: "3px", 
          background: "linear-gradient(90deg, #ff0080, #7928ca)", zIndex: 9999,
          animation: "loading-bar 2s infinite"
        }} />
      )}
      <Routes>
        {!user ? (
          <>
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </>
        ) : (
          <>
            <Route path="/" element={<ForYou user={user} syncVersion={syncVersion} />} />
            <Route path="/trending" element={<Trending syncVersion={syncVersion} />} />
            <Route path="/article/:id" element={<ArticleDetail user={user} />} />
            <Route path="/profile" element={<Profile user={user} onLogout={handleLogout} />} />
            <Route path="/login" element={<Navigate to="/" replace />} />
          </>
        )}
      </Routes>
      <ToastContainer />
    </BrowserRouter>
  );
}
