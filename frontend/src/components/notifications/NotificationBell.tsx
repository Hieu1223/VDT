import React, { useState } from "react";
import { Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "@/context/NotificationContext";
import "@/components/notifications/NotificationBell.css";

export default function NotificationBell() {
  const { notifications, unreadCount, markRead, markAllRead, bellShake } = useNotifications();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleClick = async (notificationId: string, ticketId?: string | null) => {
    await markRead(notificationId);
    setOpen(false);
    if (ticketId) navigate(`/tickets/${ticketId}`);
  };

  return (
    <div className="notification-bell-wrapper">
      <button
        className={`notification-bell-trigger ${bellShake ? "notification-bell-shake" : ""}`}
        data-testid="notification-bell-button"
        onClick={() => setOpen((o) => !o)}
      >
        <Bell size={20} />
        {unreadCount > 0 && <span className="notification-bell-count" data-testid="notification-unread-count">{unreadCount > 9 ? "9+" : unreadCount}</span>}
      </button>

      {open && (
        <div className="notification-bell-panel" data-testid="notification-bell-panel">
          <div className="notification-bell-panel-header">
            <span className="label">Notifications</span>
            {unreadCount > 0 && (
              <button className="btn btn-ghost btn-sm" data-testid="notification-mark-all-read-button" onClick={() => markAllRead()}>
                Mark all read
              </button>
            )}
          </div>
          <div className="notification-bell-list">
            {notifications.length === 0 && <p className="text-muted notification-bell-empty">No notifications yet.</p>}
            {notifications.map((n) => (
              <button
                key={n.id}
                className={`notification-bell-item ${!n.read_at ? "notification-bell-item-unread" : ""}`}
                data-testid={`notification-item-${n.id}`}
                onClick={() => handleClick(n.id, n.ticket_id)}
              >
                <span className="notification-bell-item-title">{n.title}</span>
                <span className="notification-bell-item-body">{n.body}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
