import React, { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { Link } from "react-router-dom";
import { csatApi, usersApi } from "@/api/endpoints";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { exportToCsv } from "@/lib/csv";
import type { CsatSurvey, User } from "@/types";
import "@/pages/admin/Admin.css";

type RatingMode = "exact" | "range";

export default function AdminCsatPage() {
  const [surveys, setSurveys] = useState<CsatSurvey[]>([]);
  const [technicians, setTechnicians] = useState<User[]>([]);
  const [ratingMode, setRatingMode] = useState<RatingMode>("range");
  const [filters, setFilters] = useState({ status: "", technician_id: "", date_from: "", date_to: "", ratingExact: 0, ratingMin: 1, ratingMax: 5 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    usersApi.technicians().then(({ data }) => setTechnicians(data));
  }, []);

  const load = () => {
    setLoading(true);
    const params: any = {};
    if (filters.status) params.status = filters.status;
    if (filters.technician_id) params.technician_id = filters.technician_id;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    if (ratingMode === "exact" && filters.ratingExact > 0) {
      params.rating_min = filters.ratingExact;
      params.rating_max = filters.ratingExact;
    } else if (ratingMode === "range" && (filters.ratingMin > 1 || filters.ratingMax < 5)) {
      params.rating_min = filters.ratingMin;
      params.rating_max = filters.ratingMax;
    }
    csatApi.adminList(params).then(({ data }) => setSurveys(data)).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.status, filters.technician_id, filters.date_from, filters.date_to, filters.ratingExact, filters.ratingMin, filters.ratingMax, ratingMode]);

  const handleExport = () => {
    exportToCsv("csat-surveys", surveys, [
      { key: "ticket_subject", label: "Ticket" },
      { key: "requester_username", label: "Requester" },
      { key: "technician_username", label: "Technician" },
      { key: "rating", label: "Rating" },
      { key: "comment", label: "Comment" },
      { key: "status", label: "Status" },
      { key: "submitted_at", label: "Submitted At" },
    ]);
  };

  return (
    <div className="page" data-testid="admin-csat-page">
      <div className="page-header">
        <div>
          <h1>CSAT Surveys</h1>
          <p className="text-muted">Every customer satisfaction survey, with filters across rating, technician, and date.</p>
        </div>
        <button className="btn btn-secondary" data-testid="admin-csat-export-csv-button" onClick={handleExport} disabled={surveys.length === 0}>
          <Download size={16} /> Export CSV
        </button>
      </div>

      <div className="admin-filters card">
        <select className="select" value={filters.status} data-testid="admin-csat-status-filter" onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="submitted">Submitted</option>
        </select>
        <select className="select" value={filters.technician_id} data-testid="admin-csat-technician-filter" onChange={(e) => setFilters((f) => ({ ...f, technician_id: e.target.value }))}>
          <option value="">All technicians</option>
          {technicians.map((t) => <option key={t.id} value={t.id}>{t.full_name} ({t.username})</option>)}
        </select>
        <input type="date" className="input" data-testid="admin-csat-date-from-input" value={filters.date_from} onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))} />
        <input type="date" className="input" data-testid="admin-csat-date-to-input" value={filters.date_to} onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))} />

        <div className="range-slider-field">
          <div className="range-slider-dual">
            <label className="label">Rating</label>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              data-testid="admin-csat-rating-mode-toggle"
              onClick={() => setRatingMode((m) => (m === "exact" ? "range" : "exact"))}
            >
              {ratingMode === "exact" ? "Switch to range" : "Switch to exact"}
            </button>
          </div>
          {ratingMode === "exact" ? (
            <select className="select" value={filters.ratingExact} data-testid="admin-csat-rating-exact-select" onChange={(e) => setFilters((f) => ({ ...f, ratingExact: Number(e.target.value) }))}>
              <option value={0}>Any rating</option>
              {[1, 2, 3, 4, 5].map((r) => <option key={r} value={r}>{r} star{r > 1 ? "s" : ""}</option>)}
            </select>
          ) : (
            <>
              <span className="range-slider-value">Min: {filters.ratingMin} - Max: {filters.ratingMax}</span>
              <input type="range" min={1} max={5} value={filters.ratingMin} data-testid="admin-csat-rating-min-slider"
                onChange={(e) => setFilters((f) => ({ ...f, ratingMin: Math.min(Number(e.target.value), f.ratingMax) }))} />
              <input type="range" min={1} max={5} value={filters.ratingMax} data-testid="admin-csat-rating-max-slider"
                onChange={(e) => setFilters((f) => ({ ...f, ratingMax: Math.max(Number(e.target.value), f.ratingMin) }))} />
            </>
          )}
        </div>
      </div>

      {loading ? (
        <LoadingSpinner fullPage />
      ) : surveys.length === 0 ? (
        <EmptyState title="No CSAT surveys match your filters" testId="admin-csat-empty" />
      ) : (
        <div className="table-wrapper card">
          <table className="data-table" data-testid="admin-csat-table">
            <thead>
              <tr><th>Ticket</th><th>Requester</th><th>Technician</th><th>Rating</th><th>Comment</th><th>Status</th><th>Submitted</th></tr>
            </thead>
            <tbody>
              {surveys.map((s) => (
                <tr key={s.id} data-testid={`admin-csat-row-${s.id}`}>
                  <td><Link to={`/tickets/${s.ticket_id}`} className="ticket-subject-link">{s.ticket_subject || s.ticket_id.slice(0, 8)}</Link></td>
                  <td>{s.requester_username || "-"}</td>
                  <td>{s.technician_username || "-"}</td>
                  <td className="mono">{s.rating != null ? `${s.rating} / 5` : "-"}</td>
                  <td>{s.comment || "-"}</td>
                  <td><span className={`status-pill request-status-${s.status === "submitted" ? "approved" : "pending"}`}>{s.status}</span></td>
                  <td>{s.submitted_at ? new Date(s.submitted_at).toLocaleString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
