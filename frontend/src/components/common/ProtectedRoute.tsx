import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { UserRole } from "@/types";

interface Props {
  children: React.ReactElement;
  allowedRoles?: UserRole[];
}

export default function ProtectedRoute({ children, allowedRoles }: Props) {
  const { user, loading } = useAuth();

  if (loading) return <LoadingSpinner fullPage />;
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  return children;
}
