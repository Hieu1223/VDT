import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { filtersApi, timelineApi, ticketsApi } from "@/api/endpoints";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import PriorityBadge from "@/components/badges/PriorityBadge";
import type { Ticket, TimelineEvent } from "@/types";
import "@/pages/admin/Admin.css";

type ViewMode = "calendar" | "events";

interface FilterOptions {
  statuses: string[];
  priorities: string[];
  technicians: { id: string; username: string; full_name: string }[];
}

export default function TimelinePage() {
  const [mode, setMode] = useState<ViewMode>("calendar");
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [options, setOptions] = useState<FilterOptions>({ statuses: [], priorities: [], technicians: [] });
  const [filters, setFilters] = useState({ status: "", priority: "", assignee_id: "", date_from: "", date_to: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    filtersApi.ticketOptions().then(({ data }) => setOptions(data));
  }, []);

  const loadCalendar = () => {
    const params: any = {};
    if (filters.status) params.status = filters.status;
    if (filters.priority) params.priority = filters.priority;
    if (filters.assignee_id) params.assignee_id = filters.assignee_id;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    return ticketsApi.all(params).then(({ data }) => setTickets(data));
  };

  const loadEvents = () => timelineApi.list({ limit: 200 }).then(({ data }) => setEvents(data));

  useEffect(() => {
    setLoading(true);
    const loader = mode === "calendar" ? loadCalendar() : loadEvents();
    loader.finally(() => setLoading(false));
    const interval = setInterval(() => (mode === "calendar" ? loadCalendar() : loadEvents()), 15000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, filters.status, filters.priority, filters.assignee_id, filters.date_from, filters.date_to]);

  const fmt = (v?: string | null) => (v ? new Date(v).toLocaleString() : "-");

  return (
    <div className="page" data-testid="timeline-page">
      <div className="page-header">
        <div>
          <h1>Timeline</h1>
          <p className="text-muted">Calendar view of every ticket&apos;s lifecycle, or the raw chronological event log.</p>
        </div>
        <div className="timeline-mode-toggle">
          <button
            className={`btn btn-sm ${mode === "calendar" ? "btn-primary" : "btn-secondary"}`}
            data-testid="timeline-mode-calendar-button"
            onClick={() => setMode("calendar")}
          >
            Ticket Calendar
          </button>
          <button
            className={`btn btn-sm ${mode === "events" ? "btn-primary" : "btn-secondary"}`}
            data-testid="timeline-mode-events-button"
            onClick={() => setMode("events")}
          >
            Raw Event Log
          </button>
        </div>
      </div>

      {mode === "calendar" && (
        <div className="admin-filters card">
          <select className="select" value={filters.status} data-testid="timeline-status-filter" onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
            <option value="">All statuses</option>
            {options.statuses.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
          </select>
          <select className="select" value={filters.priority} data-testid="timeline-priority-filter" onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}>
            <option value="">All priorities</option>
            {options.priorities.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <select className="select" value={filters.assignee_id} data-testid="timeline-handler-filter" onChange={(e) => setFilters((f) => ({ ...f, assignee_id: e.target.value }))}>
            <option value="">All handlers</option>
            {options.technicians.map((t) => <option key={t.id} value={t.id}>{t.full_name} ({t.username})</option>)}
          </select>
          <input type="date" className="input" data-testid="timeline-date-from-input" value={filters.date_from} onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))} />
          <input type="date" className="input" data-testid="timeline-date-to-input" value={filters.date_to} onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))} />
        </div>
      )}

      {loading ? (
        <LoadingSpinner fullPage />
      ) : mode === "calendar" ? (
        tickets.length === 0 ? (
          <EmptyState title="No tickets match your filters" testId="timeline-calendar-empty" />
        ) : (
          <div className="table-wrapper card">
            <table className="data-table timeline-calendar-table" data-testid="timeline-calendar-table">
              <thead>
                <tr>
                  <th>Ticket</th><th>Priority</th><th>Handler</th><th>Created</th>
                  <th>First response due</th><th>Resolve due</th><th>Resolved</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr key={t.id} data-testid={`timeline-calendar-row-${t.id}`}>
                    <td><Link to={`/tickets/${t.id}`} className="ticket-subject-link">{t.subject}</Link></td>
                    <td><PriorityBadge priority={t.priority} /></td>
                    <td>{t.assignee_username || "Unassigned"}</td>
                    <td>{fmt(t.created_at)}</td>
                    <td>{fmt(t.sla?.first_response_due_at)}</td>
                    <td>{fmt(t.sla?.resolve_due_at)}</td>
                    <td>{fmt(t.sla?.resolved_at)}</td>
                    <td><span className={`status-pill status-pill-${t.status}`}>{t.status.replace("_", " ")}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : events.length === 0 ? (
        <EmptyState title="No events yet" testId="timeline-empty" />
      ) : (
        <div className="timeline-list card">
          {events.map((e) => (
            <div className="timeline-item" key={e.id} data-testid={`timeline-item-${e.id}`}>
              <span className="mono timeline-item-key">{e.routing_key}</span>
              <span className="text-muted timeline-item-time">{new Date(e.created_at).toLocaleString()}</span>
              {e.ticket_id && <span className="timeline-item-ticket text-muted">ticket #{e.ticket_id.slice(0, 8)}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
