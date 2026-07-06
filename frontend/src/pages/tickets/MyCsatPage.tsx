import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { csatApi, usersApi } from "@/api/endpoints";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { Pagination } from "@/components/common/Pagination";
import { RangeSlider } from "@/components/common/RangeSlider";
import type { CsatSurvey, User } from "@/types";
import "@/pages/admin/Admin.css";

type RatingMode = "exact" | "range";
const PAGE_SIZE = 20;

export default function MyCsatPage() {
  const [surveys, setSurveys] = useState<CsatSurvey[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [technicians, setTechnicians] = useState<User[]>([]);
  const [ratingMode, setRatingMode] = useState<RatingMode>("range");
  const [filters, setFilters] = useState({ status: "", technician_id: "", date_from: "", date_to: "", ratingExact: 0, ratingRange: [1, 5] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    usersApi.technicians().then(({ data }) => setTechnicians(data));
  }, []);

  const load = () => {
    setLoading(true);
    const params: any = { page, page_size: PAGE_SIZE };
    if (filters.status) params.status = filters.status;
    if (filters.technician_id) params.technician_id = filters.technician_id;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    if (ratingMode === "exact" && filters.ratingExact > 0) {
      params.rating_min = filters.ratingExact;
      params.rating_max = filters.ratingExact;
    } else if (ratingMode === "range" && (filters.ratingRange[0] > 1 || filters.ratingRange[1] < 5)) {
      params.rating_min = filters.ratingRange[0];
      params.rating_max = filters.ratingRange[1];
    }
    csatApi.adminList(params).then(({ data }) => { setSurveys(data.items); setTotal(data.total); }).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filters.status, filters.technician_id, filters.date_from, filters.date_to, filters.ratingExact, filters.ratingRange, ratingMode]);

  useEffect(() => { setPage(1); }, [filters.status, filters.technician_id, filters.date_from, filters.date_to, filters.ratingExact, filters.ratingRange, ratingMode]);

  return (
    <div className="page" data-testid="my-csat-page">
      <div className="page-header">
        <div>
          <h1>My CSAT Surveys</h1>
          <p className="text-muted">Satisfaction surveys for tickets you&apos;ve submitted.</p>
        </div>
      </div>

      <div className="admin-filters card">
        <select className="select" value={filters.status} data-testid="my-csat-status-filter" onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="submitted">Submitted</option>
        </select>
        <select className="select" value={filters.technician_id} data-testid="my-csat-technician-filter" onChange={(e) => setFilters((f) => ({ ...f, technician_id: e.target.value }))}>
          <option value="">All technicians</option>
          {technicians.map((t) => <option key={t.id} value={t.id}>{t.full_name} ({t.username})</option>)}
        </select>
        <input type="date" className="input" data-testid="my-csat-date-from-input" value={filters.date_from} onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))} />
        <input type="date" className="input" data-testid="my-csat-date-to-input" value={filters.date_to} onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))} />
        <div className="range-slider-field">
          <div className="range-slider-dual">
            <label className="label">Rating</label>
            <button type="button" className="btn btn-ghost btn-sm" data-testid="my-csat-rating-mode-toggle" onClick={() => setRatingMode((m) => (m === "exact" ? "range" : "exact"))}>
              {ratingMode === "exact" ? "Switch to range" : "Switch to exact"}
            </button>
          </div>
          {ratingMode === "exact" ? (
            <select className="select" value={filters.ratingExact} data-testid="my-csat-rating-exact-select" onChange={(e) => setFilters((f) => ({ ...f, ratingExact: Number(e.target.value) }))}>
              <option value={0}>Any rating</option>
              {[1, 2, 3, 4, 5].map((r) => <option key={r} value={r}>{r} star{r > 1 ? "s" : ""}</option>)}
            </select>
          ) : (
            <>
              <span className="range-slider-value">Min: {filters.ratingRange[0]} - Max: {filters.ratingRange[1]}</span>
              <RangeSlider min={1} max={5} step={1} value={filters.ratingRange} testId="my-csat-rating-range-slider" onValueChange={(v) => setFilters((f) => ({ ...f, ratingRange: v }))} />
            </>
          )}
        </div>
      </div>

      {loading ? (
        <LoadingSpinner fullPage />
      ) : surveys.length === 0 ? (
        <EmptyState title="No CSAT surveys yet" testId="my-csat-empty" />
      ) : (
        <div className="table-wrapper card">
          <table className="data-table" data-testid="my-csat-table">
            <thead>
              <tr><th>Ticket</th><th>Technician</th><th>Rating</th><th>Comment</th><th>Status</th><th>Submitted</th></tr>
            </thead>
            <tbody>
              {surveys.map((s) => (
                <tr key={s.id} data-testid={`my-csat-row-${s.id}`}>
                  <td><Link to={`/tickets/${s.ticket_id}`} className="ticket-subject-link">{s.ticket_subject || s.ticket_id.slice(0, 8)}</Link></td>
                  <td>{s.technician_username || "-"}</td>
                  <td className="mono">{s.rating != null ? `${s.rating} / 5` : "-"}</td>
                  <td>{s.comment || "-"}</td>
                  <td><span className={`status-pill request-status-${s.status === "submitted" ? "approved" : "pending"}`}>{s.status}</span></td>
                  <td>{s.submitted_at ? new Date(s.submitted_at).toLocaleString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} testId="my-csat-pagination" />
        </div>
      )}
    </div>
  );
}
