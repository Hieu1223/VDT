import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import dayjs, { Dayjs } from "dayjs";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";
import { filtersApi, ticketsApi, usersApi } from "@/api/endpoints";
import type { Ticket, User } from "@/types";
import "@/pages/admin/TimelineCalendar.css";

const ROW_COLORS = ["#003BFF", "#E11D48", "#F59E0B", "#10B981", "#7C3AED", "#0EA5E9", "#DB2777", "#059669", "#EA580C", "#4338CA"];
const ZOOM_LEVELS = [90, 120, 150, 190, 240, 300];
const DEFAULT_ZOOM_INDEX = 2;
const UNASSIGNED_ROW_ID = "__unassigned__";

interface Row {
  id: string;
  label: string;
  color: string;
}

interface Bar {
  ticket: Ticket;
  leftPx: number;
  widthPx: number;
}

function startOfWeek(d: Dayjs): Dayjs {
  const dow = d.day(); // 0 = Sunday
  const diff = dow === 0 ? -6 : 1 - dow; // Monday-start week
  return d.add(diff, "day").startOf("day");
}

export default function TimelineCalendar() {
  const navigate = useNavigate();
  const [weekOffset, setWeekOffset] = useState(0);
  const [zoomIndex, setZoomIndex] = useState(DEFAULT_ZOOM_INDEX);
  const [technicians, setTechnicians] = useState<User[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [hiddenRows, setHiddenRows] = useState<Set<string>>(new Set());
  const [options, setOptions] = useState<{ statuses: string[]; priorities: string[] }>({ statuses: [], priorities: [] });
  const [filters, setFilters] = useState({ status: "", priority: "" });
  const [loading, setLoading] = useState(true);

  const dayColWidth = ZOOM_LEVELS[zoomIndex];
  const weekStart = useMemo(() => startOfWeek(dayjs()).add(weekOffset, "week"), [weekOffset]);
  const weekEnd = useMemo(() => weekStart.add(6, "day").endOf("day"), [weekStart]);
  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => weekStart.add(i, "day")), [weekStart]);

  useEffect(() => {
    usersApi.technicians().then(({ data }) => setTechnicians(data));
    filtersApi.ticketOptions().then(({ data }) => setOptions({ statuses: data.statuses, priorities: data.priorities }));
  }, []);

  useEffect(() => {
    setLoading(true);
    const params: any = {
      date_from: weekStart.subtract(45, "day").format("YYYY-MM-DD"),
      date_to: weekEnd.format("YYYY-MM-DD"),
      page_size: 500,
    };
    if (filters.status) params.status = filters.status;
    if (filters.priority) params.priority = filters.priority;
    ticketsApi.all(params).then(({ data }) => setTickets(data.items)).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [weekStart, filters.status, filters.priority]);

  const rows: Row[] = useMemo(() => {
    const techRows = technicians.map((t, i) => ({ id: t.id, label: `${t.full_name}`, color: ROW_COLORS[i % ROW_COLORS.length] }));
    return [{ id: UNASSIGNED_ROW_ID, label: "Unassigned queue", color: "#71717A" }, ...techRows];
  }, [technicians]);

  const barsByRow: Record<string, Bar[]> = useMemo(() => {
    const map: Record<string, Bar[]> = {};
    const rangeStartMs = weekStart.valueOf();
    const rangeEndMs = weekEnd.valueOf();
    const totalMs = rangeEndMs - rangeStartMs;

    for (const ticket of tickets) {
      const rowId = ticket.assignee_id || UNASSIGNED_ROW_ID;
      const startMs = dayjs(ticket.created_at).valueOf();
      const endMs = ticket.sla?.resolved_at ? dayjs(ticket.sla.resolved_at).valueOf() : dayjs().valueOf();
      if (endMs < rangeStartMs || startMs > rangeEndMs) continue;

      const clippedStart = Math.max(startMs, rangeStartMs);
      const clippedEnd = Math.min(endMs, rangeEndMs);
      const leftPx = ((clippedStart - rangeStartMs) / totalMs) * (dayColWidth * 7);
      const widthPx = Math.max(((clippedEnd - clippedStart) / totalMs) * (dayColWidth * 7), 28);

      if (!map[rowId]) map[rowId] = [];
      map[rowId].push({ ticket, leftPx, widthPx });
    }
    return map;
  }, [tickets, weekStart, weekEnd, dayColWidth]);

  const toggleRow = (rowId: string) => {
    setHiddenRows((prev) => {
      const next = new Set(prev);
      if (next.has(rowId)) next.delete(rowId);
      else next.add(rowId);
      return next;
    });
  };

  const zoomIn = () => setZoomIndex((i) => Math.min(i + 1, ZOOM_LEVELS.length - 1));
  const zoomOut = () => setZoomIndex((i) => Math.max(i - 1, 0));

  const visibleRows = rows.filter((r) => !hiddenRows.has(r.id));
  const totalWidth = dayColWidth * 7;

  return (
    <div className="gantt-container" data-testid="timeline-gantt">
      <div className="gantt-toolbar">
        <div className="gantt-nav">
          <button className="btn btn-secondary btn-sm" data-testid="gantt-prev-week-button" onClick={() => setWeekOffset((w) => w - 1)}>
            <ChevronLeft size={16} />
          </button>
          <button className="btn btn-secondary btn-sm" data-testid="gantt-today-button" onClick={() => setWeekOffset(0)}>Today</button>
          <button className="btn btn-secondary btn-sm" data-testid="gantt-next-week-button" onClick={() => setWeekOffset((w) => w + 1)}>
            <ChevronRight size={16} />
          </button>
          <span className="gantt-range-label" data-testid="gantt-range-label">
            {weekStart.format("MMM D")} - {weekEnd.format("MMM D, YYYY")}
          </span>
        </div>
        <div className="gantt-zoom-controls">
          <span className="label">Zoom</span>
          <button className="btn btn-secondary btn-sm" data-testid="gantt-zoom-out-button" onClick={zoomOut} disabled={zoomIndex === 0}>
            <ZoomOut size={16} />
          </button>
          <button className="btn btn-secondary btn-sm" data-testid="gantt-zoom-in-button" onClick={zoomIn} disabled={zoomIndex === ZOOM_LEVELS.length - 1}>
            <ZoomIn size={16} />
          </button>
        </div>
        <div className="admin-filters gantt-filters">
          <select className="select" value={filters.status} data-testid="gantt-status-filter" onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
            <option value="">All statuses</option>
            {options.statuses.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
          </select>
          <select className="select" value={filters.priority} data-testid="gantt-priority-filter" onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}>
            <option value="">All priorities</option>
            {options.priorities.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>

      <div className="gantt-body-wrapper">
        <div className="gantt-sidebar">
          <div className="gantt-sidebar-header-spacer" />
          {rows.map((row) => (
            <button
              key={row.id}
              className={`gantt-legend-row ${hiddenRows.has(row.id) ? "gantt-legend-row-hidden" : ""}`}
              data-testid={`gantt-legend-${row.id}`}
              onClick={() => toggleRow(row.id)}
              style={{ "--row-color": row.color } as React.CSSProperties}
            >
              <span className="gantt-legend-dot" />
              {row.label}
              <span className="gantt-legend-count">{barsByRow[row.id]?.length || 0}</span>
            </button>
          ))}
        </div>

        <div className="gantt-scroll-area">
          <div className="gantt-date-header" style={{ width: totalWidth }}>
            {days.map((d) => (
              <div key={d.toString()} className={`gantt-date-col ${d.isSame(dayjs(), "day") ? "gantt-date-col-today" : ""}`} style={{ width: dayColWidth }}>
                <span className="gantt-date-col-dow">{d.format("ddd")}</span>
                <span className="gantt-date-col-num">{d.format("D")}</span>
              </div>
            ))}
          </div>

          <div className="gantt-rows" style={{ width: totalWidth }}>
            {loading ? (
              <div className="gantt-loading">Loading timeline...</div>
            ) : (
              visibleRows.map((row) => (
                <div key={row.id} className="gantt-row" data-testid={`gantt-row-${row.id}`}>
                  {days.map((d) => <div key={d.toString()} className="gantt-row-col" style={{ width: dayColWidth }} />)}
                  {(barsByRow[row.id] || []).map((bar) => (
                    <div
                      key={bar.ticket.id}
                      className="gantt-bar"
                      data-testid={`gantt-bar-${bar.ticket.id}`}
                      style={{ left: bar.leftPx, width: bar.widthPx, background: row.color }}
                      title={`${bar.ticket.priority} · ${bar.ticket.subject}`}
                      onClick={() => navigate(`/tickets/${bar.ticket.id}`)}
                    >
                      <span className="gantt-bar-priority">{bar.ticket.priority}</span>
                      <span className="gantt-bar-subject">{bar.ticket.subject}</span>
                    </div>
                  ))}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
