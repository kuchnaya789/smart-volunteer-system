import React from "react";
import { Navigate, Outlet } from "react-router-dom";

export default function ProtectedRoute({ requiredRole, allowedRoles }) {
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");

  const roles = Array.isArray(allowedRoles) && allowedRoles.length > 0 ? allowedRoles : requiredRole ? [requiredRole] : [];

  if (!token) return <Navigate to="/" replace />;
  if (roles.length > 0 && !roles.includes(role)) return <Navigate to="/" replace />;

  return <Outlet />;
}

