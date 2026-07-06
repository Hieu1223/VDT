import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { filtersApi, ticketsApi } from "@/api/endpoints";
import PriorityBadge from "@/components/badges/PriorityBadge";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { Ticket } from "@/types";
import "@/pages/admin/Admin.css";

export default function AllTicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [options, setOptions] = useState<{ statuses: string[]; priorities: string[] }>({ statuses: [], priorities: [] });
  const [filters, setFilters] = useState({ status: "", priority: "", search: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    filtersApi.ticketOptions().then(({ data }) => setOptions(data));
  }, []);

  const load = () => {
    setLoading(true);
    const params: any = {};
    if (filters.status) params.status = filters.status;
    if (filters.priority) params.priority = filters.priority;
    if (filters.search) params.search = filters.search;
    ticketsApi.all(params).then(({ data }) => setTickets(data)).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.status, filters.priority]);

  return (
    <div className="page" data-testid="all-tickets-page">
      <div className="page-header">
        <div>
          <h1>All Tickets</h1>
          <p className="text-muted">Browse every ticket in the system.</p>
        </div>
      </div>

      <div className="admin-filters card">
        <input
          className="input"
          placeholder="Search subject..."
          value={filters.search}
          data-testid="all-tickets-search-input"
          onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <select className="select" value={filters.status} data-testid="all-tickets-status-filter" onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
          <option value="">All statuses</option>
          {options.statuses.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
        </select>
        <select className="select" value={filters.priority} data-testid="all-tickets-priority-filter" onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}>
          <option value="">All priorities</option>
          {options.priorities.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <button className="btn btn-secondary btn-sm" data-testid="all-tickets-search-button" onClick={load}>Search</button>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : tickets.length === 0 ? (
        <EmptyState title="No tickets match your filters" testId="all-tickets-empty" />
      ) : (
        <div className="table-wrapper card">
          <table className="data-table" data-testid="all-tickets-table">
            <thead>
              <tr>
                <th>Subject</th><th>Requester</th><th>Assignee</th><th>Priority</th><th>Status</th><th>Created</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} data-testid={`all-tickets-row-${t.id}`}>
                  <td><Link to={`/tickets/${t.id}`} className="ticket-subject-link">{t.subject}</Link></td>
                  <td>{t.requester_username}</td>
                  <td>{t.assignee_username || "Unassigned"}</td>
                  <td><PriorityBadge priority={t.priority} /></td>
                  <td><span className={`status-pill status-pill-${t.status}`}>{t.status.replace("_", " ")}</span></td>
                  <td>{new Date(t.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
