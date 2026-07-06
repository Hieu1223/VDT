import React from "react";
import type { TicketStatus } from "@/types";
import "@/components/badges/Badges.css";

const STEPS: { key: TicketStatus; label: string }[] = [
  { key: "new", label: "New" },
  { key: "assigned", label: "Assigned" },
  { key: "in_progress", label: "In Progress" },
  { key: "resolved", label: "Resolved" },
];

export default function StatusStepper({ status }: { status: TicketStatus }) {
  if (status === "rejected" || status === "closed") {
    return (
      <div className="status-stepper" data-testid="status-stepper-terminal">
        <span className="status-terminal-badge">{status === "rejected" ? "Rejected" : "Closed"}</span>
      </div>
    );
  }

  const effectiveStatus = status === "escalated" ? "in_progress" : status;
  const currentIndex = STEPS.findIndex((s) => s.key === effectiveStatus);

  return (
    <div className="status-stepper" data-testid="status-stepper">
      {STEPS.map((step, idx) => (
        <React.Fragment key={step.key}>
          <div className={`status-step ${idx <= currentIndex ? "status-step-active" : ""} ${idx === currentIndex ? "status-step-current" : ""}`}>
            <span className="status-step-dot" />
            <span className="status-step-label">{step.label}</span>
          </div>
          {idx < STEPS.length - 1 && <span className={`status-step-connector ${idx < currentIndex ? "status-step-connector-active" : ""}`} />}
        </React.Fragment>
      ))}
      {status === "escalated" && <span className="status-escalated-flag" data-testid="status-escalated-flag">Escalated</span>}
    </div>
  );
}
