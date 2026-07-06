import React from "react";
import type { Priority } from "@/types";
import "@/components/badges/Badges.css";

const LABELS: Record<Priority, string> = { P1: "P1 · Critical", P2: "P2 · High", P3: "P3 · Medium", P4: "P4 · Low" };
const CLASS: Record<Priority, string> = { P1: "priority-badge-high", P2: "priority-badge-high", P3: "priority-badge-medium", P4: "priority-badge-low" };

export default function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span className={`priority-badge ${CLASS[priority]}`} data-testid={`priority-badge-${priority}`}>
      {LABELS[priority]}
    </span>
  );
}
