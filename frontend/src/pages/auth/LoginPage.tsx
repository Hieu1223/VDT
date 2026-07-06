import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/api/client";
import "@/pages/auth/Auth.css";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(username.trim().toLowerCase(), password);
      navigate("/");
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (detail === "account_pending_activation") {
        navigate("/pending");
        return;
      }
      setError(formatApiError(detail) || "Login failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-panel fade-in">
        <div className="auth-brand">
          <span className="app-sidebar-brand-mark">HD</span>
          <span>Helpdesk / ITSM</span>
        </div>
        <h1>Welcome back</h1>
        <p className="text-muted">Sign in to manage tickets and support requests.</p>

        {error && <div className="form-error" data-testid="login-error-message">{error}</div>}

        <form onSubmit={handleSubmit} data-testid="login-form">
          <div className="field">
            <label className="label" htmlFor="login-username">Username</label>
            <input id="login-username" className="input" data-testid="login-username-input" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
          </div>
          <div className="field">
            <label className="label" htmlFor="login-password">Password</label>
            <input id="login-password" type="password" className="input" data-testid="login-password-input" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary auth-submit" data-testid="login-submit-button" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="auth-footer-link text-muted">
          Don&apos;t have an account? <Link to="/register" data-testid="login-register-link">Register</Link>
        </p>
      </div>
      <div className="auth-hero" />
    </div>
  );
}
