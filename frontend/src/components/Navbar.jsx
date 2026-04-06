import React from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

function RoleBadge({ role }) {
  const label = role === "ngo" ? "NGO" : role === "student" ? "Student" : role === "admin" ? "Admin" : "";
  if (!label) return null;
  return (
    <span className="ml-2 inline-flex items-center rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white ring-1 ring-white/25">
      {label}
    </span>
  );
}

export default function Navbar() {
  const navigate = useNavigate();
  const auth = useAuth();
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");
  const name = localStorage.getItem("name") || "";

  const links = [];
  if (token && role === "ngo") {
    links.push(
      { to: "/ngo/dashboard", label: "Dashboard" },
      { to: "/ngo/create-task", label: "Create Task" },
      { to: "/ngo/assignments", label: "Assignments" }
    );
  }
  if (token && role === "admin") {
    links.push(
      { to: "/admin/dashboard", label: "Admin" },
      { to: "/ngo/dashboard", label: "NGO Dashboard" },
      { to: "/ngo/create-task", label: "Create Task" },
      { to: "/ngo/assignments", label: "Assignments" },
      { to: "/student/dashboard", label: "Student Dashboard" },
      { to: "/student/profile", label: "Student Profile" },
      { to: "/student/tasks", label: "My Tasks" }
    );
  }
  if (token && role === "student") {
    links.push(
      { to: "/student/dashboard", label: "Dashboard" },
      { to: "/student/profile", label: "Profile" },
      { to: "/student/tasks", label: "My Tasks" }
    );
  }

  const onLogout = () => {
    auth?.logout?.();
    navigate("/", { replace: true });
  };

  return (
    <header className="bg-[#1E3A8A] text-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link to="/" className="text-lg font-bold tracking-tight">
          Smart Volunteer Allocation System
        </Link>

        <nav className="flex items-center gap-6">
          {links.length > 0 && (
            <div className="hidden items-center gap-4 md:flex">
              {links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  className={({ isActive }) =>
                    `text-sm font-semibold ${isActive ? "underline underline-offset-4" : "hover:underline hover:underline-offset-4"}`
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </div>
          )}

          {token ? (
            <div className="flex items-center gap-3">
              <div className="hidden items-center md:flex">
                <span className="text-sm font-semibold">{name || "User"}</span>
                <RoleBadge role={role} />
              </div>
              <button
                onClick={onLogout}
                className="bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <NavLink
                to="/ngo/login"
                className="bg-white/10 hover:bg-white/15 text-white rounded-lg px-4 py-2 text-sm font-semibold"
              >
                NGO Login
              </NavLink>
              <NavLink
                to="/student/login"
                className="bg-white/10 hover:bg-white/15 text-white rounded-lg px-4 py-2 text-sm font-semibold"
              >
                Student Login
              </NavLink>
              <NavLink
                to="/admin/login"
                className="bg-white/10 hover:bg-white/15 text-white rounded-lg px-4 py-2 text-sm font-semibold"
              >
                Admin
              </NavLink>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

