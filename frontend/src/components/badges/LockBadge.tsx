import React from "react";
import { Lock, LockOpen } from "lucide-react";
import type { LockBlock } from "@/types";
import "@/components/badges/Badges.css";

export default function LockBadge({ lock, currentUserId }: { lock?: LockBlock | null; currentUserId?: string }) {
  const isLocked = !!lock?.locked_by;
  if (!isLocked) {
    return (
      <span className="lock-badge lock-badge-open" data-testid="lock-badge-unlocked">
        <LockOpen size={14} /> Unlocked
      </span>
    );
  }
  const isMine = lock?.locked_by === currentUserId;
  return (
    <span className={`lock-badge ${isMine ? "lock-badge-mine" : "lock-badge-other"}`} data-testid="lock-badge-locked">
      <Lock size={14} /> {isMine ? "Locked by you" : `Locked by ${lock?.locked_by_username}`}
    </span>
  );
}
