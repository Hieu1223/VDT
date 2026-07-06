import React from "react";
import { Link } from "react-router-dom";
import { Clock } from "lucide-react";
import "@/pages/auth/Auth.css";

export default function PendingActivationPage() {
  return (
    <div className="auth-page">
      <div className="auth-panel fade-in" data-testid="pending-activation-page">
        <div className="auth-brand">
          <span className="app-sidebar-brand-mark">HD</span>
          <span>Helpdesk / ITSM</span>
        </div>
        <div className="pending-icon"><Clock size={40} /></div>
        <h1>Account pending activation</h1>
        <p className="text-muted">
          Thanks for registering. An administrator needs to review and activate your account before you can sign in.
          Please check back shortly.
        </p>
        <Link to="/login" className="btn btn-primary auth-submit" data-testid="pending-back-to-login-link">Back to sign in</Link>
      </div>
      <div className="auth-hero" />
    </div>
  );
}
