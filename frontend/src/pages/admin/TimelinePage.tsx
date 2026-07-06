import React, { useEffect, useState } from "react";
import { timelineApi } from "@/api/endpoints";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import TimelineCalendar from "@/pages/admin/TimelineCalendar";
import type { TimelineEvent } from "@/types";
import "@/pages/admin/Admin.css";

type ViewMode = "calendar" | "events";

export default function TimelinePage() {
  const [mode, setMode] = useState<ViewMode>("calendar");
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadEvents = () => timelineApi.list({ limit: 200 }).then(({ data }) => setEvents(data));

  useEffect(() => {
    if (mode !== "events") return;
    setLoading(true);
    loadEvents().finally(() => setLoading(false));
    const interval = setInterval(loadEvents, 15000);
    return () => clearInterval(interval);
  }, [mode]);

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

      {mode === "calendar" ? (
        <TimelineCalendar />
      ) : loading ? (
        <LoadingSpinner fullPage />
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
