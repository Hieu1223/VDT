import React, { useState } from "react";
import { usersApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import "@/pages/settings/Settings.css";

export default function AccountSettingsPage() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [profileMsg, setProfileMsg] = useState("");
  const [profileError, setProfileError] = useState("");
  const [passwordMsg, setPasswordMsg] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg("");
    setProfileError("");
    try {
      await usersApi.updateProfile({ full_name: fullName, email });
      await refreshUser();
      setProfileMsg("Profile updated.");
    } catch (err: any) {
      setProfileError(formatApiError(err?.response?.data?.detail) || "Could not update profile.");
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg("");
    setPasswordError("");
    try {
      await usersApi.changePassword(currentPassword, newPassword);
      setPasswordMsg("Password changed.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: any) {
      setPasswordError(formatApiError(err?.response?.data?.detail) || "Could not change password.");
    }
  };

  return (
    <div className="page" data-testid="account-settings-page">
      <div className="page-header">
        <div>
          <h1>Account Settings</h1>
          <p className="text-muted">Manage your profile and password.</p>
        </div>
      </div>

      <div className="settings-grid">
        <form className="card settings-form" onSubmit={handleProfileSave} data-testid="settings-profile-form">
          <h3>Profile</h3>
          {profileMsg && <div className="settings-success" data-testid="settings-profile-success">{profileMsg}</div>}
          {profileError && <div className="form-error" data-testid="settings-profile-error">{profileError}</div>}

          <div className="field">
            <label className="label" htmlFor="settings-fullname">Full name</label>
            <input id="settings-fullname" className="input" data-testid="settings-fullname-input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="field">
            <label className="label" htmlFor="settings-email">Email</label>
            <input id="settings-email" type="email" className="input" data-testid="settings-email-input" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <label className="settings-toggle settings-presence-note">
            <span className="text-muted">
              Online status is automatic - you&apos;re shown as online while this app is open (no manual toggle needed).
            </span>
          </label>
          <button type="submit" className="btn btn-primary" data-testid="settings-profile-save-button">Save profile</button>
        </form>

        <form className="card settings-form" onSubmit={handlePasswordChange} data-testid="settings-password-form">
          <h3>Change password</h3>
          {passwordMsg && <div className="settings-success" data-testid="settings-password-success">{passwordMsg}</div>}
          {passwordError && <div className="form-error" data-testid="settings-password-error">{passwordError}</div>}

          <div className="field">
            <label className="label" htmlFor="settings-current-password">Current password</label>
            <input id="settings-current-password" type="password" className="input" data-testid="settings-current-password-input" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
          </div>
          <div className="field">
            <label className="label" htmlFor="settings-new-password">New password</label>
            <input id="settings-new-password" type="password" className="input" data-testid="settings-new-password-input" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={6} />
          </div>
          <button type="submit" className="btn btn-primary" data-testid="settings-password-save-button">Update password</button>
        </form>
      </div>
    </div>
  );
}
