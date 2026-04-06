import React, { useEffect, useMemo, useState } from "react";
import api from "../../api/axios.js";
import ScoreBreakdown from "../../components/ScoreBreakdown.jsx";

function StatusBadge({ status }) {
  const s = (status || "open").toLowerCase();
  const base = "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1";
  const cls =
    s === "completed"
      ? "bg-green-50 text-green-700 ring-green-200"
      : s === "assigned"
        ? "bg-blue-50 text-blue-700 ring-blue-200"
        : "bg-gray-50 text-gray-700 ring-gray-200";
  return <span className={`${base} ${cls}`}>{s.toUpperCase()}</span>;
}

function UrgencyBadge({ urgency01 }) {
  const u = Number(urgency01);
  const v = Number.isFinite(u) ? Math.round(u * 10) : 5;
  const label = v <= 3 ? "LOW" : v <= 5 ? "MEDIUM" : v <= 8 ? "HIGH" : "CRITICAL";
  const base = "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1";
  const cls =
    v <= 3
      ? "bg-green-50 text-green-700 ring-green-200"
      : v <= 5
        ? "bg-yellow-50 text-yellow-700 ring-yellow-200"
        : v <= 8
          ? "bg-orange-50 text-orange-700 ring-orange-200"
          : "bg-red-50 text-red-700 ring-red-200";
  return <span className={`${base} ${cls}`}>{label}</span>;
}

export default function ViewAssignments() {
  const role = typeof window !== "undefined" ? localStorage.getItem("role") || "" : "";
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState(() => new Set());
  const [completing, setCompleting] = useState(() => new Set());
  const [assigning, setAssigning] = useState(() => new Set());
  const [deleting, setDeleting] = useState(() => new Set());

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/assignments/ngo-assignments");
      const arr = Array.isArray(res.data) ? res.data : res.data?.tasks || res.data?.assignments || [];
      setItems(arr);
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to load assignments.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggle = (id) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const markComplete = async (taskId) => {
    setCompleting((prev) => new Set(prev).add(taskId));
    setError("");
    try {
      await api.put(`/tasks/${taskId}/complete`);
      await load();
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to mark task complete.");
    } finally {
      setCompleting((prev) => {
        const next = new Set(prev);
        next.delete(taskId);
        return next;
      });
    }
  };

  const deleteTask = async (taskId) => {
    const ok = window.confirm("Delete this task? Assignments and related activity rows for this task will be removed.");
    if (!ok) return;
    setDeleting((prev) => new Set(prev).add(taskId));
    setError("");
    try {
      await api.delete(`/tasks/${taskId}`);
      await load();
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to delete task.");
    } finally {
      setDeleting((prev) => {
        const next = new Set(prev);
        next.delete(taskId);
        return next;
      });
    }
  };

  const assignNow = async (taskId) => {
    setAssigning((prev) => new Set(prev).add(taskId));
    setError("");
    try {
      await api.post(`/assignments/run/${taskId}`);
      await load();
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "AI assignment failed.");
    } finally {
      setAssigning((prev) => {
        const next = new Set(prev);
        next.delete(taskId);
        return next;
      });
    }
  };

  const normalized = useMemo(() => {
    return items.map((x) => {
      const task = x.task || x;
      const volunteer = x.assigned_volunteer || task.assigned_volunteer || x.volunteer || task.volunteer || null;
      const scoreBreakdown = x.score_breakdown || task.score_breakdown || x.scoreBreakdown || null;
      const allCandidates = x.all_scores || task.all_scores || x.allCandidates || [];
      return {
        _id: task._id,
        title: task.title,
        urgency: task.urgency ?? task.urgency_norm,
        status: task.status || (volunteer ? "assigned" : "open"),
        taskPointsPossible: Number(task.total_points_possible ?? task.totalPossiblePoints ?? 0) || 0,
        volunteer,
        volunteerAictePoints: Number(volunteer?.aicte_points ?? 0) || 0,
        scoreBreakdown,
        allCandidates,
        ngo: x.ngo || null,
      };
    });
  }, [items]);

  return (
    <div className="bg-white min-h-screen">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-2xl font-extrabold text-gray-900">Assignments</div>
          <div className="mt-1 text-sm text-gray-700">Review ranked candidates, score breakdown, and completion status.</div>
        </div>
        <button
          onClick={load}
          className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2 text-sm font-semibold"
          type="button"
        >
          Refresh
        </button>
      </div>

      {error && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {loading ? (
        <div className="mt-6 text-sm text-gray-700">Loading...</div>
      ) : normalized.length === 0 ? (
        <div className="mt-6 bg-blue-50 border border-blue-100 rounded-xl shadow p-6 text-sm text-gray-700">
          No tasks found.
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          {normalized.map((t) => {
            const isExpanded = expanded.has(t._id);
            const canComplete = (t.status || "").toLowerCase() === "assigned";
            const canAssign = (t.status || "").toLowerCase() === "open";
            const isCompleting = completing.has(t._id);
            const isAssigning = assigning.has(t._id);
            const isDeleting = deleting.has(t._id);
            return (
              <div key={t._id} className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  <div>
                    <div className="text-lg font-extrabold text-gray-900">{t.title}</div>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <UrgencyBadge urgency01={t.urgency ?? 0.5} />
                      <StatusBadge status={t.status} />
                    </div>
                    <div className="mt-3 text-sm text-gray-700">
                      Task AICTE Value:{" "}
                      <span className="font-semibold text-gray-900">{t.taskPointsPossible.toFixed(2)} points</span>
                    </div>

                    {role === "admin" && t.ngo && (
                      <div className="mt-2 text-sm text-gray-700">
                        NGO:{" "}
                        <span className="font-semibold text-gray-900">
                          {t.ngo.name || t.ngo.email || t.ngo._id}
                        </span>
                      </div>
                    )}

                    {t.volunteer && (
                      <div className="mt-4 text-sm text-gray-700">
                        Assigned Volunteer:{" "}
                        <span className="font-semibold text-gray-900">
                          {t.volunteer?.name || t.volunteer?.full_name || t.volunteer?.email}
                        </span>
                        {t.volunteer?.email && (
                          <span className="text-gray-700">
                            {" "}
                            (<span className="font-semibold">{t.volunteer.email}</span>)
                          </span>
                        )}
                        <div className="mt-1">
                          Volunteer AICTE Score:{" "}
                          <span className="font-semibold text-gray-900">{t.volunteerAictePoints.toFixed(2)}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => toggle(t._id)}
                      className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2"
                      type="button"
                    >
                      {isExpanded ? "Hide Score Breakdown" : "Show Score Breakdown"}
                    </button>

                    {canAssign && (
                      <button
                        disabled={isAssigning}
                        onClick={() => assignNow(t._id)}
                        className="bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2 disabled:opacity-60"
                        type="button"
                      >
                        {isAssigning ? "Assigning..." : "Assign Now"}
                      </button>
                    )}

                    {canComplete && (
                      <button
                        disabled={isCompleting}
                        onClick={() => markComplete(t._id)}
                        className="bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2 disabled:opacity-60"
                        type="button"
                      >
                        {isCompleting ? "Marking..." : "Mark Complete"}
                      </button>
                    )}

                    <button
                      disabled={isDeleting}
                      onClick={() => deleteTask(t._id)}
                      className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"
                      type="button"
                    >
                      {isDeleting ? "Deleting..." : "Delete Task"}
                    </button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-6">
                    <ScoreBreakdown scoreBreakdown={t.scoreBreakdown} allCandidates={t.allCandidates} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

