import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ticketsApi } from "@/api/endpoints";
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ticketsApi.queue().then(({ data }) => setTickets(data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="queue-page">
      <div className="page-header">
        <div>
          <h1>Queue</h1>
          <p className="text-muted">Actionable tickets assigned to you or awaiting pickup.</p>
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
