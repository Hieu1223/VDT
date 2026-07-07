import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutGrid, Ticket, PlusCircle, Settings, Users, Tags, GitBranch, Activity, KanbanSquare, ListTree, Sliders, LogOut, Star, RefreshCw,
} from "lucide-react";
import { escalationApi, ticketsApi } from "@/api/endpoints";
import { useAuth } from "@/context/AuthContext";
import { useNotifications } from "@/context/NotificationContext";
import NotificationBell from "@/components/notifications/NotificationBell";
import "@/components/layout/AppShell.css";

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  count?: number;
}

const OPEN_STATUSES = ["new", "assigned", "in_progress", "escalated"];

export default function AppShell() {
  const { user, logout } = useAuth();
  const { wsError, retryConnection, reloadPage } = useNotifications();
  const navigate = useNavigate();
  const location = useLocation();
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    if (!user) return;
    const loadCount = () => {
      if (user.role === "employee") {
        ticketsApi.mine().then(({ data }) => setCount(data.filter((t) => OPEN_STATUSES.includes(t.status)).length)).catch(() => {});
      } else if (user.role === "technician_human" || user.role === "technician_virtual") {
        ticketsApi.queue().then(({ data }) => setCount(data.length)).catch(() => {});
      } else if (user.role === "admin") {
        escalationApi.pending().then(({ data }) => setCount(data.length)).catch(() => {});
      }
    };
    loadCount();
    const interval = setInterval(loadCount, 20000);
    return () => clearInterval(interval);
  }, [user]);

  if (!user) return null;

  let navItems: NavItem[] = [];
  if (user.role === "employee") {
    navItems = [
      { to: "/tickets", label: "My Tickets", icon: <Ticket size={18} />, count: count ?? undefined },
      { to: "/tickets/new", label: "New Ticket", icon: <PlusCircle size={18} /> },
      { to: "/csat", label: "My CSAT", icon: <Star size={18} /> },
    ];
  } else if (user.role === "technician_human" || user.role === "technician_virtual") {
    navItems = [
      { to: "/queue", label: "Queue", icon: <LayoutGrid size={18} />, count: count ?? undefined },
      { to: "/my-escalations", label: "My Requests", icon: <GitBranch size={18} /> },
    ];
  } else if (user.role === "admin") {
    navItems = [
      { to: "/admin/monitor", label: "Monitor", icon: <Activity size={18} />, count: count ?? undefined },
      { to: "/admin/kanban", label: "Kanban", icon: <KanbanSquare size={18} /> },
      { to: "/admin/timeline", label: "Timeline", icon: <ListTree size={18} /> },
      { to: "/admin/tickets", label: "All Tickets", icon: <Ticket size={18} /> },
      { to: "/admin/tickets/new", label: "New Ticket", icon: <PlusCircle size={18} /> },
      { to: "/admin/users", label: "Users", icon: <Users size={18} /> },
      { to: "/admin/tags", label: "Tags", icon: <Tags size={18} /> },
      { to: "/admin/csat", label: "CSAT", icon: <Star size={18} /> },
      { to: "/admin/config", label: "Assignment Config", icon: <Sliders size={18} /> },
    ];
  }

  const routeLabel = [...navItems, { to: "/settings", label: "Settings", icon: null }].find(
    (item) => location.pathname === item.to || location.pathname.startsWith(`${item.to}/`)
  )?.label || (location.pathname.startsWith("/tickets/") ? "Ticket Detail" : "");

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <aside className="app-sidebar" data-testid="app-sidebar">
        <div className="app-sidebar-brand">
          <span className="app-sidebar-brand-mark">HD</span>
          <span className="app-sidebar-brand-name">Helpdesk</span>
        </div>
        <nav className="app-sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              data-testid={`nav-link-${item.to.replace(/\//g, "-")}`}
              className={({ isActive }) => `app-sidebar-link ${isActive ? "app-sidebar-link-active" : ""}`}
            >
              {item.icon}
              <span>{item.label}</span>
              {!!item.count && <span className="app-sidebar-link-count" data-testid={`nav-count-${item.to.replace(/\//g, "-")}`}>{item.count}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="app-sidebar-footer">
          <NavLink to="/settings" data-testid="nav-link-settings" className={({ isActive }) => `app-sidebar-link ${isActive ? "app-sidebar-link-active" : ""}`}>
            <Settings size={18} />
            <span>Settings</span>
          </NavLink>
          <button className="app-sidebar-link app-sidebar-logout" data-testid="logout-button" onClick={handleLogout}>
            <LogOut size={18} />
            <span>Log out</span>
          </button>
        </div>
      </aside>

      <div className="app-main">
        <header className="app-topbar">
          <span className="app-topbar-route-name" data-testid="topbar-route-name">{routeLabel}</span>
          <div className="app-topbar-right">
            <div className="app-topbar-user" data-testid="topbar-current-user">
              <span className="app-topbar-username">{user.full_name}</span>
              <span className="app-topbar-role label">{user.role.replace("_", " ")}</span>
            </div>
            <NotificationBell />
          </div>
        </header>
        {wsError && (
          <div className="ws-alert-banner" data-testid="ws-alert-banner">
            <span className="ws-alert-text">Live notifications are unavailable. You may miss updates.</span>
            <button className="btn btn-secondary btn-sm" data-testid="ws-alert-retry-button" onClick={retryConnection}>
              <RefreshCw size={14} /> Try Again
            </button>
            <button className="btn btn-primary btn-sm" data-testid="ws-alert-reload-button" onClick={reloadPage}>
              Reload Page
            </button>
          </div>
        )}
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
