import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { getAccessToken, getWsUrl } from "@/api/client";
import { notificationsApi } from "@/api/endpoints";
import { useAuth } from "@/context/AuthContext";
import type { Notification } from "@/types";

interface NotificationContextValue {
  notifications: Notification[];
  unreadCount: number;
  markRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
  bellShake: boolean;
  ticketEventTick: number;
}

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [bellShake, setBellShake] = useState(false);
  const [ticketEventTick, setTicketEventTick] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!user) {
      setNotifications([]);
      return;
    }
    notificationsApi.list().then(({ data }) => setNotifications(data)).catch(() => {});
  }, [user]);

  useEffect(() => {
    if (!user) return;
    const token = getAccessToken();
    if (!token) return;

    const ws = new WebSocket(getWsUrl(token));
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.kind === "notification") {
          setNotifications((prev) => [msg.data, ...prev]);
          setBellShake(true);
          setTimeout(() => setBellShake(false), 700);
        } else if (msg.kind === "ticket_event") {
          setTicketEventTick((t) => t + 1);
        }
      } catch {
        // ignore malformed frames
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [user]);

  const markRead = useCallback(async (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n)));
    await notificationsApi.markRead(id);
  }, []);

  const markAllRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read_at: n.read_at || new Date().toISOString() })));
    await notificationsApi.markAllRead();
  }, []);

  const unreadCount = notifications.filter((n) => !n.read_at).length;

  const value = useMemo(
    () => ({ notifications, unreadCount, markRead, markAllRead, bellShake, ticketEventTick }),
    [notifications, unreadCount, markRead, markAllRead, bellShake, ticketEventTick]
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export function useNotifications(): NotificationContextValue {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used within NotificationProvider");
  return ctx;
}
