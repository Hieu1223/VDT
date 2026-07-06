import React from "react";

export default function EmptyState({ title, subtitle, testId }: { title: string; subtitle?: string; testId?: string }) {
  return (
    <div className="empty-state" data-testid={testId || "empty-state"}>
      <h3>{title}</h3>
      {subtitle && <p className="text-muted">{subtitle}</p>}
    </div>
  );
}
