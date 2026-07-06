import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/api/client";
import "@/pages/auth/Auth.css";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "", full_name: "", email: "", role: "employee" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register({ ...form, username: form.username.trim().toLowerCase() });
      navigate("/pending");
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Registration failed.");
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
        <h1>Create your account</h1>
        <p className="text-muted">An admin will need to activate your account before you can sign in.</p>

        {error && <div className="form-error" data-testid="register-error-message">{error}</div>}

        <form onSubmit={handleSubmit} data-testid="register-form">
          <div className="field">
            <label className="label" htmlFor="register-fullname">Full name</label>
            <input id="register-fullname" className="input" data-testid="register-fullname-input" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} required />
          </div>
          <div className="field">
            <label className="label" htmlFor="register-username">Username</label>
            <input id="register-username" className="input" data-testid="register-username-input" value={form.username} onChange={(e) => update("username", e.target.value)} required minLength={3} />
          </div>
          <div className="field">
            <label className="label" htmlFor="register-email">Email (optional)</label>
            <input id="register-email" type="email" className="input" data-testid="register-email-input" value={form.email} onChange={(e) => update("email", e.target.value)} />
          </div>
          <div className="field">
            <label className="label" htmlFor="register-password">Password</label>
            <input id="register-password" type="password" className="input" data-testid="register-password-input" value={form.password} onChange={(e) => update("password", e.target.value)} required minLength={6} />
          </div>
          <div className="field">
            <label className="label" htmlFor="register-role">I am a</label>
            <select id="register-role" className="select" data-testid="register-role-select" value={form.role} onChange={(e) => update("role", e.target.value)}>
              <option value="employee">Employee (submit tickets)</option>
              <option value="technician_human">Technician (handle tickets)</option>
            </select>
          </div>
          <button type="submit" className="btn btn-primary auth-submit" data-testid="register-submit-button" disabled={submitting}>
            {submitting ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="auth-footer-link text-muted">
          Already have an account? <Link to="/login" data-testid="register-login-link">Sign in</Link>
        </p>
      </div>
      <div className="auth-hero" />
    </div>
  );
}
