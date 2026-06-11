import { NavLink } from "react-router-dom";
import { Newspaper, Sparkles, Flame } from "lucide-react";

export default function Navbar({ user, onLogout }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand-wrap">
        <div className="navbar-logo">
          <Newspaper size={24} color="var(--accent)" />
        </div>
        <span className="navbar-brand">FeedMe</span>
      </div>

      <NavLink
        to="/"
        className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
        end
      >
        <Sparkles size={18} /> For You
      </NavLink>

      <NavLink
        to="/trending"
        className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
      >
        <Flame size={18} /> Trending
      </NavLink>

      <NavLink
        to="/profile"
        className={({ isActive }) => "user-avatar" + (isActive ? " active" : "")}
        title={user.name}
      >
        {user.name.substring(0, 2).toUpperCase()}
      </NavLink>
    </nav>
  );
}
