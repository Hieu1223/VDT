import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { escalationApi } from "@/api/endpoints";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { EscalationRequest } from "@/types";
import "@/pages/technician/Technician.css";

export default function MyEscalationsPage() {
  const [requests, setRequests] = useState<EscalationRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    escalationApi.mine().then(({ data }) => setRequests(data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="my-escalations-page">
      <div className="page-header">
        <div>
          <h1>My Requests</h1>
          <p className="text-muted">Escalation and reassignment requests you&apos;ve raised.</p>
        </div>
      </div>

      {requests.length === 0 ? (
        <EmptyState title="No requests yet" subtitle="Escalate or request reassignment from a ticket's detail page." testId="my-escalations-empty" />
      ) : (
        <div className="table-wrapper card">
          <table className="data-table" data-testid="my-escalations-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Ticket</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Review note</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id} data-testid={`escalation-row-${r.id}`}>
                  <td className="mono">{r.type}</td>
                  <td><Link to={`/tickets/${r.ticket_id}`} data-testid={`escalation-ticket-link-${r.id}`}>View ticket</Link></td>
                  <td>{r.reason}</td>
                  <td><span className={`status-pill request-status-${r.status}`}>{r.status}</span></td>
                  <td className="text-muted">{r.review_note || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
