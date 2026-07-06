import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { filtersApi, ticketsApi } from "@/api/endpoints";
import PriorityBadge from "@/components/badges/PriorityBadge";
import LockBadge from "@/components/badges/LockBadge";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { useAuth } from "@/context/AuthContext";
import type { Ticket } from "@/types";
import "@/pages/technician/Technician.css";

export default function QueuePage() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [tagOptions, setTagOptions] = useState<{ name: string; color: string }[]>([]);
  const [filters, setFilters] = useState({ tag: "", date_from: "", date_to: "", sla_min_pct: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    filtersApi.ticketOptions().then(({ data }) => setTagOptions(data.tags));
  }, []);

  const load = () => {
    setLoading(true);
    const params: any = {};
    if (filters.tag) params.tag = filters.tag;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    if (filters.sla_min_pct > 0) params.sla_min_pct = filters.sla_min_pct;
    ticketsApi.queue(params).then(({ data }) => setTickets(data)).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.tag, filters.date_from, filters.date_to, filters.sla_min_pct]);

  if (loading && tickets.length === 0) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="queue-page">
      <div className="page-header">
        <div>
          <h1>Queue</h1>
          <p className="text-muted">Actionable tickets assigned to you or awaiting pickup.</p>
        </div>
      </div>

      <div className="admin-filters card">
        <select className="select" value={filters.tag} data-testid="queue-tag-filter" onChange={(e) => setFilters((f) => ({ ...f, tag: e.target.value }))}>
          <option value="">All tags</option>
          {tagOptions.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
        </select>
        <input type="date" className="input" data-testid="queue-date-from-input" value={filters.date_from} onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))} />
        <input type="date" className="input" data-testid="queue-date-to-input" value={filters.date_to} onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))} />
        <div className="range-slider-field">
          <label className="label">SLA elapsed &ge; {filters.sla_min_pct}%</label>
          <input
            type="range" min={0} max={100} step={5}
            value={filters.sla_min_pct}
            data-testid="queue-sla-slider"
            onChange={(e) => setFilters((f) => ({ ...f, sla_min_pct: Number(e.target.value) }))}
          />
        </div>
      </div>

      {tickets.length === 0 ? (
        <EmptyState title="Queue is empty" subtitle="Nothing actionable right now. Nice work!" testId="queue-empty" />
      ) : (
        <div className="queue-grid">
          {tickets.map((t) => (
            <Link to={`/tickets/${t.id}`} key={t.id} className="queue-card card" data-testid={`queue-card-${t.id}`}>
              <div className="queue-card-header">
                <PriorityBadge priority={t.priority} />
                <LockBadge lock={t.lock} currentUserId={user?.id} />
              </div>
              <h3>{t.subject}</h3>
              <p className="text-muted queue-card-description">{t.description}</p>
              <div className="queue-card-footer">
                <span className={`status-pill status-pill-${t.status}`}>{t.status.replace("_", " ")}</span>
                <span className="text-muted">{t.assignee_username || "Unassigned"}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
