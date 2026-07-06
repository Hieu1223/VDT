import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { kanbanApi } from "@/api/endpoints";
import PriorityBadge from "@/components/badges/PriorityBadge";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import "@/pages/admin/Admin.css";

const COLUMN_LABELS: Record<string, string> = {
  new: "New", assigned: "Assigned", in_progress: "In Progress", escalated: "Escalated",
  resolved: "Resolved", rejected: "Rejected", closed: "Closed",
};

export default function KanbanPage() {
  const [board, setBoard] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(true);

  const load = () => kanbanApi.board().then(({ data }) => setBoard(data));

  useEffect(() => {
    load().finally(() => setLoading(false));
    const interval = setInterval(load, 20000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="kanban-page">
      <div className="page-header">
        <div>
          <h1>Kanban Board</h1>
          <p className="text-muted">Live view of every ticket by status.</p>
        </div>
      </div>

      <div className="kanban-board">
        {Object.entries(COLUMN_LABELS).map(([status, label]) => (
          <div className="kanban-column" key={status} data-testid={`kanban-column-${status}`}>
            <div className="kanban-column-header">
              <span className="label">{label}</span>
              <span className="kanban-column-count">{board[status]?.length || 0}</span>
            </div>
            <div className="kanban-column-cards">
              {(board[status] || []).map((card) => (
                <Link to={`/tickets/${card.id}`} key={card.id} className="kanban-card" data-testid={`kanban-card-${card.id}`}>
                  <PriorityBadge priority={card.priority} />
                  <h4>{card.subject}</h4>
                  <div className="kanban-card-footer text-muted">
                    <span>{card.assignee_username || "Unassigned"}</span>
                  </div>
                  {card.tags?.length > 0 && (
                    <div className="kanban-card-tags">
                      {card.tags.map((t: string) => <span key={t} className="tag-chip">{t}</span>)}
                    </div>
                  )}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
