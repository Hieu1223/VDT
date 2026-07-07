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
  wsError: boolean;
  retryConnection: () => void;
  reloadPage: () => void;
}

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [bellShake, setBellShake] = useState(false);
  const [ticketEventTick, setTicketEventTick] = useState(0);
  const [wsError, setWsError] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const reconnectAttemptsRef = useRef(0);
  const generationRef = useRef(0);
  const wsErrorTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    if (!user) {
      setNotifications([]);
      setWsError(false);
      return;
    }
    notificationsApi.list().then(({ data }) => setNotifications(data)).catch(() => {});
  }, [user]);

  const closeWs = useCallback((ws: WebSocket | null) => {
    if (!ws) return;
    try { ws.close(); } catch { /* ignore */ }
  }, []);

  const retryConnection = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    if (wsErrorTimerRef.current) {
      clearTimeout(wsErrorTimerRef.current);
      wsErrorTimerRef.current = undefined;
    }
    setWsError(false);
    closeWs(wsRef.current);
    wsRef.current = null;
  }, [closeWs, setWsError]);

  const reloadPage = useCallback(() => {
    window.location.reload();
  }, []);

  useEffect(() => {
    if (!user) return;

    const connect = () => {
      const currentToken = getAccessToken();
      if (!currentToken) return;
      const ws = new WebSocket(getWsUrl(currentToken));
      const generation = generationRef.current;
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setWsError(false);
        if (wsErrorTimerRef.current) {
          clearTimeout(wsErrorTimerRef.current);
          wsErrorTimerRef.current = undefined;
        }
      };

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

      ws.onerror = () => {
        // onclose will fire after onerror; do not reconnect here
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (generation === generationRef.current && user) {
          const delay = Math.min(1000 * 2 ** reconnectAttemptsRef.current, 30000);
          reconnectAttemptsRef.current += 1;
          reconnectTimerRef.current = setTimeout(() => {
            if (generation === generationRef.current && user) connect();
          }, delay);
          if (!wsErrorTimerRef.current) {
            wsErrorTimerRef.current = setTimeout(() => {
              setWsError(true);
            }, 10000);
          }
        }
      };
    };

    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = undefined;
      }
      if (wsErrorTimerRef.current) {
        clearTimeout(wsErrorTimerRef.current);
        wsErrorTimerRef.current = undefined;
      }
      reconnectAttemptsRef.current = 0;
      generationRef.current += 1;
      closeWs(wsRef.current);
      wsRef.current = null;
    };
  }, [user, closeWs]);

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
    () => ({ notifications, unreadCount, markRead, markAllRead, bellShake, ticketEventTick, wsError, retryConnection, reloadPage }),
    [notifications, unreadCount, markRead, markAllRead, bellShake, ticketEventTick, wsError, retryConnection, reloadPage]
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export function useNotifications(): NotificationContextValue {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used within NotificationProvider");
  return ctx;
}
