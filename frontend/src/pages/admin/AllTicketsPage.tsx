import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Download } from "lucide-react";
import { filtersApi, ticketsApi, usersApi } from "@/api/endpoints";
import PriorityBadge from "@/components/badges/PriorityBadge";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { Pagination } from "@/components/common/Pagination";
import { RangeSlider } from "@/components/common/RangeSlider";
import { exportToCsv } from "@/lib/csv";
import type { Ticket, User } from "@/types";
import "@/pages/admin/Admin.css";

const PAGE_SIZE = 20;

export default function AllTicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [technicians, setTechnicians] = useState<User[]>([]);
  const [options, setOptions] = useState<{ statuses: string[]; priorities: string[]; tags: { name: string; color: string }[] }>({ statuses: [], priorities: [], tags: [] });
  const [filters, setFilters] = useState({ status: "", priority: "", search: "", tag: "", assignee_id: "", date_from: "", date_to: "", sla_min_pct: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    filtersApi.ticketOptions().then(({ data }) => setOptions(data));
    usersApi.technicians().then(({ data }) => setTechnicians(data));
  }, []);

  const load = () => {
    setLoading(true);
    const params: any = { page, page_size: PAGE_SIZE };
    if (filters.status) params.status = filters.status;
    if (filters.priority) params.priority = filters.priority;
    if (filters.search) params.search = filters.search;
    if (filters.tag) params.tag = filters.tag;
    if (filters.assignee_id) params.assignee_id = filters.assignee_id;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    if (filters.sla_min_pct > 0) params.sla_min_pct = filters.sla_min_pct;
    ticketsApi.all(params).then(({ data }) => { setTickets(data.items); setTotal(data.total); }).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filters.status, filters.priority, filters.tag, filters.assignee_id, filters.date_from, filters.date_to, filters.sla_min_pct]);

  useEffect(() => { setPage(1); }, [filters.status, filters.priority, filters.tag, filters.assignee_id, filters.date_from, filters.date_to, filters.sla_min_pct]);

  const handleExport = () => {
    exportToCsv("all-tickets", tickets, [
      { key: "id", label: "ID" },
      { key: "subject", label: "Subject" },
      { key: "requester_username", label: "Requester" },
      { key: "assignee_username", label: "Assignee" },
      { key: "priority", label: "Priority" },
      { key: "status", label: "Status" },
      { key: "created_at", label: "Created At" },
    ]);
  };

  return (
    <div className="page" data-testid="all-tickets-page">
      <div className="page-header">
        <div>
          <h1>All Tickets</h1>
          <p className="text-muted">Browse every ticket in the system.</p>
        </div>
        <button className="btn btn-secondary" data-testid="all-tickets-export-csv-button" onClick={handleExport} disabled={tickets.length === 0}>
          <Download size={16} /> Export CSV
        </button>
      </div>

      <div className="admin-filters card">
        <input
          className="input"
          placeholder="Search subject..."
          value={filters.search}
          data-testid="all-tickets-search-input"
          onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
          onKeyDown={(e) => e.key === "Enter" && (setPage(1), load())}
        />
        <select className="select" value={filters.status} data-testid="all-tickets-status-filter" onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
          <option value="">All statuses</option>
          {options.statuses.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
        </select>
        <select className="select" value={filters.priority} data-testid="all-tickets-priority-filter" onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}>
          <option value="">All priorities</option>
          {options.priorities.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <select className="select" value={filters.tag} data-testid="all-tickets-tag-filter" onChange={(e) => setFilters((f) => ({ ...f, tag: e.target.value }))}>
          <option value="">All tags</option>
          {options.tags.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
        </select>
        <select className="select" value={filters.assignee_id} data-testid="all-tickets-handler-filter" onChange={(e) => setFilters((f) => ({ ...f, assignee_id: e.target.value }))}>
          <option value="">All handlers</option>
          <option value="unassigned">Unassigned queue</option>
          {technicians.map((t) => <option key={t.id} value={t.id}>{t.full_name} ({t.username})</option>)}
        </select>
        <input type="date" className="input" data-testid="all-tickets-date-from-input" value={filters.date_from} onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))} />
        <input type="date" className="input" data-testid="all-tickets-date-to-input" value={filters.date_to} onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))} />
        <div className="range-slider-field">
          <label className="label">SLA elapsed &ge; {filters.sla_min_pct}%</label>
          <RangeSlider min={0} max={100} step={5} value={[filters.sla_min_pct]} testId="all-tickets-sla-slider" onValueChange={([v]) => setFilters((f) => ({ ...f, sla_min_pct: v }))} />
        </div>
        <button className="btn btn-secondary btn-sm" data-testid="all-tickets-search-button" onClick={() => { setPage(1); load(); }}>Search</button>
      </div>

      {loading ? (
        <LoadingSpinner fullPage />
      ) : tickets.length === 0 ? (
        <EmptyState title="No tickets match your filters" testId="all-tickets-empty" />
      ) : (
        <div className="table-wrapper card">
          <table className="data-table" data-testid="all-tickets-table">
            <thead>
              <tr><th>Subject</th><th>Requester</th><th>Handler</th><th>Priority</th><th>Status</th><th>Created</th></tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} data-testid={`all-tickets-row-${t.id}`}>
                  <td><Link to={`/tickets/${t.id}`} className="ticket-subject-link">{t.subject}</Link></td>
                  <td>{t.requester_username}</td>
                  <td>{t.assignee_username || "Unassigned"}</td>
                  <td><PriorityBadge priority={t.priority} /></td>
                  <td><span className={`status-pill status-pill-${t.status}`}>{t.status.replace("_", " ")}</span></td>
                  <td>{new Date(t.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} testId="all-tickets-pagination" />
        </div>
      )}
    </div>
  );
}
