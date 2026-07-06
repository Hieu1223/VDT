import React, { useEffect, useState } from "react";
import { Download, UserPlus } from "lucide-react";
import { usersApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { Modal } from "@/components/common/Modal";
import { exportToCsv } from "@/lib/csv";
import type { User } from "@/types";
import "@/pages/admin/Admin.css";

const ROLE_OPTIONS = ["employee", "technician_human", "technician_virtual", "admin"];
const STATUS_OPTIONS = ["pending_activation", "active", "suspended", "deactivated"];

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ search: "", role: "", status: "", online: "", date_from: "", date_to: "" });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [form, setForm] = useState({ username: "", password: "", full_name: "", email: "", role: "technician_virtual" });
  const [creating, setCreating] = useState(false);

  const load = () => {
    const params: any = {};
    if (filters.search) params.search = filters.search;
    if (filters.role) params.role = filters.role;
    if (filters.status) params.status = filters.status;
    if (filters.online) params.online = filters.online === "true";
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    return usersApi.adminList(params).then(({ data }) => setUsers(data));
  };

  useEffect(() => {
    load().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.role, filters.status, filters.online, filters.date_from, filters.date_to]);

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
      setShowCreateModal(false);
      await load();
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not create user.");
    } finally {
      setCreating(false);
    }
  };

  const handleExport = () => {
    exportToCsv("users", users, [
      { key: "username", label: "Username" },
      { key: "full_name", label: "Full name" },
      { key: "email", label: "Email" },
      { key: "role", label: "Role" },
      { key: "status", label: "Status" },
      { key: "online", label: "Online" },
      { key: "created_at", label: "Joined" },
    ]);
  };

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="users-page">
      <div className="page-header">
        <div>
          <h1>Users</h1>
          <p className="text-muted">Activate, suspend, or deactivate accounts. Create technicians and virtual technician accounts.</p>
        </div>
        <div className="users-page-header-actions">
          <button className="btn btn-secondary" data-testid="users-export-csv-button" onClick={handleExport} disabled={users.length === 0}>
            <Download size={16} /> Export CSV
          </button>
          <button className="btn btn-primary" data-testid="users-open-create-modal-button" onClick={() => setShowCreateModal(true)}>
            <UserPlus size={16} /> Create User
          </button>
        </div>
      </div>

      {error && <div className="form-error" data-testid="users-error-message">{error}</div>}

      <div className="admin-filters card">
        <input
          className="input"
          placeholder="Search username or full name..."
          value={filters.search}
          data-testid="users-search-input"
          onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <select className="select" value={filters.role} data-testid="users-role-filter" onChange={(e) => setFilters((f) => ({ ...f, role: e.target.value }))}>
          <option value="">All roles</option>
          {ROLE_OPTIONS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <select className="select" value={filters.status} data-testid="users-status-filter" onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
        </select>
        <select className="select" value={filters.online} data-testid="users-online-filter" onChange={(e) => setFilters((f) => ({ ...f, online: e.target.value }))}>
          <option value="">Online: any</option>
          <option value="true">Online only</option>
          <option value="false">Offline only</option>
        </select>
        <input type="date" className="input" data-testid="users-date-from-input" value={filters.date_from} onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))} />
        <input type="date" className="input" data-testid="users-date-to-input" value={filters.date_to} onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))} />
        <button className="btn btn-secondary btn-sm" data-testid="users-search-button" onClick={load}>Search</button>
      </div>

      {showCreateModal && (
        <Modal title="Create user directly" onClose={() => setShowCreateModal(false)} testId="users-create-modal">
          <form onSubmit={handleCreate} data-testid="users-create-form">
            <div className="field">
              <label className="label">Username</label>
              <input className="input" value={form.username} data-testid="users-create-username-input" onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} required />
            </div>
            <div className="field">
              <label className="label">Full name</label>
              <input className="input" value={form.full_name} data-testid="users-create-fullname-input" onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} required />
            </div>
            <div className="field">
              <label className="label">Password</label>
              <input className="input" type="password" value={form.password} data-testid="users-create-password-input" onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} required minLength={6} />
            </div>
            <div className="field">
              <label className="label">Role</label>
              <select className="select" value={form.role} data-testid="users-create-role-select" onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}>
                {ROLE_OPTIONS.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <button type="submit" className="btn btn-primary" data-testid="users-create-submit-button" disabled={creating}>{creating ? "Creating..." : "Create"}</button>
          </form>
        </Modal>
      )}

      <div className="table-wrapper card">
        <table className="data-table" data-testid="users-table">
          <thead>
            <tr><th>Username</th><th>Full name</th><th>Role</th><th>Status</th><th>Online</th><th>Joined</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} data-testid={`users-row-${u.id}`}>
                <td className="mono">{u.username}</td>
                <td>{u.full_name}</td>
                <td>{u.role}</td>
                <td><span className={`status-pill request-status-${u.status === "active" ? "approved" : u.status === "pending_activation" ? "pending" : "rejected"}`}>{u.status.replace("_", " ")}</span></td>
                <td>{u.online ? "Online" : "Offline"}</td>
                <td>{new Date(u.created_at).toLocaleDateString()}</td>
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
