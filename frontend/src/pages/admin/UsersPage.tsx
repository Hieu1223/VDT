import React, { useEffect, useState } from "react";
import { usersApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { User } from "@/types";
import "@/pages/admin/Admin.css";

const ROLE_OPTIONS = ["employee", "technician_human", "technician_virtual", "admin"];

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ username: "", password: "", full_name: "", email: "", role: "technician_virtual" });
  const [creating, setCreating] = useState(false);

  const load = () => usersApi.adminList().then(({ data }) => setUsers(data));

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, []);

  const handleStatusChange = async (userId: string, status: string) => {
    setError("");
    try {
      await usersApi.adminUpdateStatus(userId, status);
      await load();
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not update status.");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setCreating(true);
    try {
      await usersApi.adminCreate(form);
      setForm({ username: "", password: "", full_name: "", email: "", role: "technician_virtual" });
      await load();
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not create user.");
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="users-page">
      <div className="page-header">
        <div>
          <h1>Users</h1>
          <p className="text-muted">Activate, suspend, or deactivate accounts. Create technicians and virtual technician accounts.</p>
        </div>
      </div>

      {error && <div className="form-error" data-testid="users-error-message">{error}</div>}

      <form className="card admin-create-user-form" onSubmit={handleCreate} data-testid="users-create-form">
        <h3>Create user directly</h3>
        <div className="admin-create-user-row">
          <input className="input" placeholder="Username" value={form.username} data-testid="users-create-username-input" onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} required />
          <input className="input" placeholder="Full name" value={form.full_name} data-testid="users-create-fullname-input" onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} required />
          <input className="input" placeholder="Password" type="password" value={form.password} data-testid="users-create-password-input" onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} required minLength={6} />
          <select className="select" value={form.role} data-testid="users-create-role-select" onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}>
            {ROLE_OPTIONS.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <button type="submit" className="btn btn-primary" data-testid="users-create-submit-button" disabled={creating}>Create</button>
        </div>
      </form>

      <div className="table-wrapper card">
        <table className="data-table" data-testid="users-table">
          <thead>
            <tr><th>Username</th><th>Full name</th><th>Role</th><th>Status</th><th>Online</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} data-testid={`users-row-${u.id}`}>
                <td className="mono">{u.username}</td>
                <td>{u.full_name}</td>
                <td>{u.role}</td>
                <td><span className={`status-pill request-status-${u.status === "active" ? "approved" : u.status === "pending_activation" ? "pending" : "rejected"}`}>{u.status.replace("_", " ")}</span></td>
                <td>{u.online ? "Online" : "Offline"}</td>
                <td className="admin-user-actions">
                  {u.status !== "active" && <button className="btn btn-secondary btn-sm" data-testid={`users-activate-${u.id}`} onClick={() => handleStatusChange(u.id, "active")}>Activate</button>}
                  {u.status !== "suspended" && <button className="btn btn-secondary btn-sm" data-testid={`users-suspend-${u.id}`} onClick={() => handleStatusChange(u.id, "suspended")}>Suspend</button>}
                  {u.status !== "deactivated" && <button className="btn btn-danger btn-sm" data-testid={`users-deactivate-${u.id}`} onClick={() => handleStatusChange(u.id, "deactivated")}>Deactivate</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
