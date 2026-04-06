import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/axios.js";

function Badge({ children, variant }) {
  const base = "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1";
  const map = {
    low: "bg-green-50 text-green-700 ring-green-200",
    medium: "bg-yellow-50 text-yellow-700 ring-yellow-200",
    high: "bg-orange-50 text-orange-700 ring-orange-200",
    critical: "bg-red-50 text-red-700 ring-red-200",
    open: "bg-gray-50 text-gray-700 ring-gray-200",
    assigned: "bg-blue-50 text-blue-700 ring-blue-200",
    completed: "bg-green-50 text-green-700 ring-green-200",
  };
  return <span className={`${base} ${map[variant] || "bg-gray-50 text-gray-700 ring-gray-200"}`}>{children}</span>;
}

function urgencyVariant(u01) {
  const u = Number(u01);
  if (!Number.isFinite(u)) return "medium";
  const v = Math.round(u * 10);
  if (v <= 3) return "low";
  if (v <= 5) return "medium";
  if (v <= 8) return "high";
  return "critical";
}

export default function NGODashboard() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/tasks");
      setTasks(Array.isArray(res.data) ? res.data : res.data?.tasks || []);
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to load tasks.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    const total = tasks.length;
    const assigned = tasks.filter((t) => (t.status || "").toLowerCase() === "assigned").length;
    const completed = tasks.filter((t) => (t.status || "").toLowerCase() === "completed").length;
    return { total, assigned, completed };
  }, [tasks]);

  return (
    <div className="bg-white min-h-screen">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-2xl font-extrabold text-gray-900">NGO Dashboard</div>
          <div className="mt-1 text-sm text-gray-700">Monitor tasks and manage AI-based assignments.</div>
        </div>
        <div className="flex gap-2">
          <Link to="/ngo/create-task" className="bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2">
            Create New Task
          </Link>
          <Link to="/ngo/assignments" className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2">
            View All Assignments
          </Link>
        </div>
      </div>

      {error && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
          <div className="text-sm font-semibold text-gray-700">Total Tasks</div>
          <div className="mt-2 text-3xl font-extrabold text-gray-900">{stats.total}</div>
        </div>
        <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
          <div className="text-sm font-semibold text-gray-700">Assigned Tasks</div>
          <div className="mt-2 text-3xl font-extrabold text-gray-900">{stats.assigned}</div>
        </div>
        <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
          <div className="text-sm font-semibold text-gray-700">Completed Tasks</div>
          <div className="mt-2 text-3xl font-extrabold text-gray-900">{stats.completed}</div>
        </div>
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
        <div className="flex items-center justify-between gap-3">
          <div className="text-lg font-extrabold text-gray-900">Recent Tasks</div>
          <button
            onClick={load}
            className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2 text-sm font-semibold"
            type="button"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="mt-4 text-sm text-gray-700">Loading tasks...</div>
        ) : tasks.length === 0 ? (
          <div className="mt-4 text-sm text-gray-700">No tasks yet. Create your first task.</div>
        ) : (
          <div className="mt-4 overflow-x-auto rounded-lg border border-blue-100 bg-white">
            <table className="min-w-full text-sm">
              <thead className="bg-[#1E3A8A] text-white">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Title</th>
                  <th className="px-4 py-3 text-left font-semibold">Urgency</th>
                  <th className="px-4 py-3 text-left font-semibold">Status</th>
                  <th className="px-4 py-3 text-left font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {tasks.slice(0, 10).map((t) => {
                  const urgency = t.urgency ?? t.urgency_norm ?? 0.5;
                  const status = (t.status || "open").toLowerCase();
                  return (
                    <tr key={t._id} className="border-t border-blue-50">
                      <td className="px-4 py-3 font-semibold text-gray-900">{t.title}</td>
                      <td className="px-4 py-3">
                        <Badge variant={urgencyVariant(urgency)}>{urgencyVariant(urgency).toUpperCase()}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={status}>{status.toUpperCase()}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        {status === "open" ? (
                          <Link
                            to="/ngo/assignments"
                            className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2 text-xs font-semibold inline-block"
                          >
                            Run / View Assignments
                          </Link>
                        ) : (
                          <Link
                            to="/ngo/assignments"
                            className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2 text-xs font-semibold inline-block"
                          >
                            View Details
                          </Link>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

