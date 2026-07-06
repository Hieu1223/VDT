import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PlusCircle } from "lucide-react";
import { filtersApi, ticketsApi } from "@/api/endpoints";
import PriorityBadge from "@/components/badges/PriorityBadge";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { Ticket } from "@/types";
import "@/pages/tickets/Tickets.css";

export default function TicketListPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [tagOptions, setTagOptions] = useState<{ name: string; color: string }[]>([]);
  const [filters, setFilters] = useState({ tag: "", date_from: "", date_to: "" });
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
    ticketsApi.mine(params).then(({ data }) => setTickets(data)).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.tag, filters.date_from, filters.date_to]);

  if (loading && tickets.length === 0) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="ticket-list-page">
      <div className="page-header">
        <div>
          <h1>My Tickets</h1>
          <p className="text-muted">Track the status of issues you&apos;ve submitted.</p>
        </div>
        <Link to="/tickets/new" className="btn btn-primary" data-testid="ticket-list-new-ticket-link">
          <PlusCircle size={16} /> New Ticket
        </Link>
      </div>

      <div className="admin-filters card">
        <select className="select" value={filters.tag} data-testid="ticket-list-tag-filter" onChange={(e) => setFilters((f) => ({ ...f, tag: e.target.value }))}>
          <option value="">All tags</option>
          {tagOptions.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
        </select>
        <input type="date" className="input" data-testid="ticket-list-date-from-input" value={filters.date_from} onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))} />
        <input type="date" className="input" data-testid="ticket-list-date-to-input" value={filters.date_to} onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))} />
      </div>

      {tickets.length === 0 ? (
        <EmptyState title="No tickets yet" subtitle="Create your first support ticket to get started." testId="ticket-list-empty" />
      ) : (
        <div className="table-wrapper card">
          <table className="data-table" data-testid="ticket-list-table">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Assignee</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} data-testid={`ticket-row-${t.id}`}>
                  <td>
                    <Link to={`/tickets/${t.id}`} className="ticket-subject-link" data-testid={`ticket-link-${t.id}`}>{t.subject}</Link>
                  </td>
                  <td>{t.category}</td>
                  <td><PriorityBadge priority={t.priority} /></td>
                  <td><span className={`status-pill status-pill-${t.status}`}>{t.status.replace("_", " ")}</span></td>
                  <td>{t.assignee_username || "Unassigned"}</td>
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
