import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { NotificationProvider } from "@/context/NotificationContext";
import ProtectedRoute from "@/components/common/ProtectedRoute";
import ErrorBoundary from "@/components/common/ErrorBoundary";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";

import LoginPage from "@/pages/auth/LoginPage";
import RegisterPage from "@/pages/auth/RegisterPage";
import PendingActivationPage from "@/pages/auth/PendingActivationPage";

import TicketListPage from "@/pages/tickets/TicketListPage";
import NewTicketPage from "@/pages/tickets/NewTicketPage";
import TicketDetailPage from "@/pages/tickets/TicketDetailPage";
import CsatPage from "@/pages/tickets/CsatPage";

import QueuePage from "@/pages/technician/QueuePage";
import MyEscalationsPage from "@/pages/technician/MyEscalationsPage";

import AccountSettingsPage from "@/pages/settings/AccountSettingsPage";

import KanbanPage from "@/pages/admin/KanbanPage";
import TimelinePage from "@/pages/admin/TimelinePage";
import AllTicketsPage from "@/pages/admin/AllTicketsPage";
import UsersPage from "@/pages/admin/UsersPage";
import TagsPage from "@/pages/admin/TagsPage";
import MonitorPage from "@/pages/admin/MonitorPage";
import ConfigPage from "@/pages/admin/ConfigPage";
import AdminCsatPage from "@/pages/admin/AdminCsatPage";

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner fullPage />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "employee") return <Navigate to="/tickets" replace />;
  if (user.role === "technician_human" || user.role === "technician_virtual") return <Navigate to="/queue" replace />;
  return <Navigate to="/admin/monitor" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationProvider>
          <ErrorBoundary>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/pending" element={<PendingActivationPage />} />

              <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
                <Route path="/" element={<HomeRedirect />} />

                <Route path="/tickets" element={<ProtectedRoute allowedRoles={["employee"]}><TicketListPage /></ProtectedRoute>} />
                <Route path="/tickets/new" element={<ProtectedRoute allowedRoles={["employee"]}><NewTicketPage /></ProtectedRoute>} />
                <Route path="/tickets/:id" element={<ProtectedRoute><TicketDetailPage /></ProtectedRoute>} />
                <Route path="/csat/:id" element={<ProtectedRoute allowedRoles={["employee"]}><CsatPage /></ProtectedRoute>} />

                <Route path="/queue" element={<ProtectedRoute allowedRoles={["technician_human", "technician_virtual"]}><QueuePage /></ProtectedRoute>} />
                <Route path="/my-escalations" element={<ProtectedRoute allowedRoles={["technician_human", "technician_virtual"]}><MyEscalationsPage /></ProtectedRoute>} />

                <Route path="/settings" element={<AccountSettingsPage />} />

                <Route path="/admin/kanban" element={<ProtectedRoute allowedRoles={["admin"]}><KanbanPage /></ProtectedRoute>} />
                <Route path="/admin/timeline" element={<ProtectedRoute allowedRoles={["admin"]}><TimelinePage /></ProtectedRoute>} />
                <Route path="/admin/tickets" element={<ProtectedRoute allowedRoles={["admin"]}><AllTicketsPage /></ProtectedRoute>} />
                <Route path="/admin/tickets/new" element={<ProtectedRoute allowedRoles={["admin"]}><NewTicketPage /></ProtectedRoute>} />
                <Route path="/admin/users" element={<ProtectedRoute allowedRoles={["admin"]}><UsersPage /></ProtectedRoute>} />
                <Route path="/admin/tags" element={<ProtectedRoute allowedRoles={["admin"]}><TagsPage /></ProtectedRoute>} />
                <Route path="/admin/monitor" element={<ProtectedRoute allowedRoles={["admin"]}><MonitorPage /></ProtectedRoute>} />
                <Route path="/admin/config" element={<ProtectedRoute allowedRoles={["admin"]}><ConfigPage /></ProtectedRoute>} />
                <Route path="/admin/csat" element={<ProtectedRoute allowedRoles={["admin"]}><AdminCsatPage /></ProtectedRoute>} />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
