import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";

import LandingPage from "./pages/LandingPage.jsx";

import NGOLogin from "./pages/auth/NGOLogin.jsx";
import NGORegister from "./pages/auth/NGORegister.jsx";
import StudentLogin from "./pages/auth/StudentLogin.jsx";
import StudentRegister from "./pages/auth/StudentRegister.jsx";

import NGODashboard from "./pages/ngo/NGODashboard.jsx";
import CreateTask from "./pages/ngo/CreateTask.jsx";
import ViewAssignments from "./pages/ngo/ViewAssignments.jsx";

import StudentDashboard from "./pages/student/StudentDashboard.jsx";
import StudentProfile from "./pages/student/StudentProfile.jsx";
import AssignedTasks from "./pages/student/AssignedTasks.jsx";

import AdminLogin from "./pages/auth/AdminLogin.jsx";
import AdminRegister from "./pages/auth/AdminRegister.jsx";
import AdminDashboard from "./pages/admin/AdminDashboard.jsx";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="bg-white min-h-screen">
          <Navbar />
          <main className="mx-auto max-w-6xl px-4 py-8">
            <Routes>
              <Route path="/" element={<LandingPage />} />

              <Route path="/ngo/register" element={<NGORegister />} />
              <Route path="/ngo/login" element={<NGOLogin />} />

              <Route path="/student/register" element={<StudentRegister />} />
              <Route path="/student/login" element={<StudentLogin />} />

              <Route path="/admin/login" element={<AdminLogin />} />
              <Route path="/admin/register" element={<AdminRegister />} />

              <Route element={<ProtectedRoute allowedRoles={["ngo", "admin"]} />}>
                <Route path="/ngo/dashboard" element={<NGODashboard />} />
                <Route path="/ngo/create-task" element={<CreateTask />} />
                <Route path="/ngo/assignments" element={<ViewAssignments />} />
              </Route>

              <Route element={<ProtectedRoute allowedRoles={["student", "admin"]} />}>
                <Route path="/student/dashboard" element={<StudentDashboard />} />
                <Route path="/student/profile" element={<StudentProfile />} />
                <Route path="/student/tasks" element={<AssignedTasks />} />
              </Route>

              <Route element={<ProtectedRoute requiredRole="admin" />}>
                <Route path="/admin/dashboard" element={<AdminDashboard />} />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

