import React, { useEffect, useState } from "react";
import { timelineApi } from "@/api/endpoints";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { TimelineEvent } from "@/types";
import "@/pages/admin/Admin.css";

export default function TimelinePage() {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => timelineApi.list({ limit: 200 }).then(({ data }) => setEvents(data));

  useEffect(() => {
    load().finally(() => setLoading(false));
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="timeline-page">
      <div className="page-header">
        <div>
          <h1>Event Log / Timeline</h1>
          <p className="text-muted">Chronological feed of every domain event across the system.</p>
        </div>
      </div>

      {events.length === 0 ? (
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
