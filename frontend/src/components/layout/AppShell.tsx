import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutGrid, Ticket, PlusCircle, Settings, Users, Tags, GitBranch, Activity, KanbanSquare, ListTree, Sliders, LogOut,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import NotificationBell from "@/components/notifications/NotificationBell";
import "@/components/layout/AppShell.css";

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

export default function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  let navItems: NavItem[] = [];
  if (user.role === "employee") {
    navItems = [
      { to: "/tickets", label: "My Tickets", icon: <Ticket size={18} /> },
      { to: "/tickets/new", label: "New Ticket", icon: <PlusCircle size={18} /> },
    ];
  } else if (user.role === "technician_human" || user.role === "technician_virtual") {
    navItems = [
      { to: "/queue", label: "Queue", icon: <LayoutGrid size={18} /> },
      { to: "/my-escalations", label: "My Requests", icon: <GitBranch size={18} /> },
    ];
  } else if (user.role === "admin") {
    navItems = [
      { to: "/admin/monitor", label: "Monitor", icon: <Activity size={18} /> },
      { to: "/admin/kanban", label: "Kanban", icon: <KanbanSquare size={18} /> },
      { to: "/admin/timeline", label: "Timeline", icon: <ListTree size={18} /> },
      { to: "/admin/tickets", label: "All Tickets", icon: <Ticket size={18} /> },
      { to: "/admin/users", label: "Users", icon: <Users size={18} /> },
      { to: "/admin/tags", label: "Tags", icon: <Tags size={18} /> },
      { to: "/admin/config", label: "Assignment Config", icon: <Sliders size={18} /> },
    ];
  }

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
          <div className="app-topbar-user" data-testid="topbar-current-user">
            <span className="app-topbar-username">{user.full_name}</span>
            <span className="app-topbar-role label">{user.role.replace("_", " ")}</span>
          </div>
          <NotificationBell />
        </header>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
