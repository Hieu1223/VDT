import React, { useEffect, useState } from "react";
import { escalationApi, monitorApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import type { EscalationRequest, User } from "@/types";
import "@/pages/admin/Admin.css";

export default function MonitorPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [pending, setPending] = useState<EscalationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [note, setNote] = useState<Record<string, string>>({});
  const [target, setTarget] = useState<Record<string, string>>({});

  const load = () => Promise.all([
    monitorApi.users().then(({ data }) => setUsers(data)),
    monitorApi.tickets().then(({ data }) => setStats(data)),
    escalationApi.pending().then(({ data }) => setPending(data)),
  ]);

  useEffect(() => {
    load().finally(() => setLoading(false));
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleReview = async (id: string, action: "approve" | "reject" | "return") => {
    setError("");
    try {
      if (action === "approve") await escalationApi.approve(id, target[id], note[id]);
      if (action === "reject") await escalationApi.reject(id, note[id]);
      if (action === "return") await escalationApi.returnToRequester(id, note[id]);
      await load();
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not review request.");
    }
  };

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="monitor-page">
      <div className="page-header">
        <div>
          <h1>Monitor</h1>
          <p className="text-muted">Live overview of users, tickets, and pending requests.</p>
        </div>
      </div>

      {error && <div className="form-error" data-testid="monitor-error-message">{error}</div>}

      {stats && (
        <div className="monitor-stats-grid">
          <StatCard label="Total tickets" value={stats.total} testId="monitor-stat-total" />
          <StatCard label="Currently locked" value={stats.currently_locked} testId="monitor-stat-locked" />
          <StatCard label="First-response breaches" value={stats.sla_first_response_breached} danger testId="monitor-stat-fr-breach" />
          <StatCard label="Resolve breaches" value={stats.sla_resolve_breached} danger testId="monitor-stat-resolve-breach" />
          <StatCard label="SLA compliance rate" value={stats.sla_compliance_rate != null ? `${stats.sla_compliance_rate}%` : "-"} testId="monitor-stat-sla-compliance" />
          <StatCard label="Avg CSAT score" value={stats.avg_csat_score != null ? `${stats.avg_csat_score} / 5` : "-"} testId="monitor-stat-avg-csat" />
        </div>
      )}

      <h3 className="monitor-section-title">Pending Escalation / Reassignment Requests</h3>
      {pending.length === 0 ? (
        <EmptyState title="No pending requests" testId="monitor-pending-empty" />
      ) : (
        <div className="monitor-pending-list">
          {pending.map((r) => (
            <div key={r.id} className="card monitor-pending-card" data-testid={`monitor-pending-${r.id}`}>
              <div className="monitor-pending-header">
                <span className="mono">{r.type}</span>
                <span className="text-muted">by {r.requested_by_username}</span>
              </div>
              <p>{r.reason}</p>
              <div className="monitor-pending-form">
                <select className="select" value={target[r.id] || r.target_technician_id || ""} data-testid={`monitor-target-select-${r.id}`} onChange={(e) => setTarget((t) => ({ ...t, [r.id]: e.target.value }))}>
                  <option value="">Select target technician (required to approve)...</option>
                  {users.filter((u) => u.role === "technician_human" || u.role === "technician_virtual").map((u) => (
                    <option key={u.id} value={u.id}>{u.full_name} ({u.username})</option>
                  ))}
                </select>
                <input className="input" placeholder="Review note (optional)" value={note[r.id] || ""} data-testid={`monitor-note-input-${r.id}`} onChange={(e) => setNote((n) => ({ ...n, [r.id]: e.target.value }))} />
                <div className="monitor-pending-actions">
                  <button className="btn btn-primary btn-sm" data-testid={`monitor-approve-${r.id}`} onClick={() => handleReview(r.id, "approve")}>Approve</button>
                  <button className="btn btn-secondary btn-sm" data-testid={`monitor-return-${r.id}`} onClick={() => handleReview(r.id, "return")}>Return</button>
                  <button className="btn btn-danger btn-sm" data-testid={`monitor-reject-${r.id}`} onClick={() => handleReview(r.id, "reject")}>Reject</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <h3 className="monitor-section-title">Users</h3>
      <div className="table-wrapper card">
        <table className="data-table" data-testid="monitor-users-table">
          <thead><tr><th>Username</th><th>Role</th><th>Status</th><th>Online</th><th>Last login</th></tr></thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} data-testid={`monitor-user-row-${u.id}`}>
                <td className="mono">{u.username}</td>
                <td>{u.role}</td>
                <td>{u.status}</td>
                <td>{u.ws_connected ? "Connected" : u.online ? "Online" : "Offline"}</td>
                <td>{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ label, value, danger, testId }: { label: string; value: number | string; danger?: boolean; testId: string }) {
  return (
    <div className={`card monitor-stat-card ${danger && Number(value) > 0 ? "monitor-stat-card-danger" : ""}`} data-testid={testId}>
      <span className="label">{label}</span>
      <span className="monitor-stat-value">{value}</span>
    </div>
  );
}
