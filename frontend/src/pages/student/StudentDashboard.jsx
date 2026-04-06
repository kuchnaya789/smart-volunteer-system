import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/axios.js";

function Tag({ children }) {
  return <span className="inline-flex items-center rounded-full bg-white px-3 py-1 text-xs font-semibold text-gray-900 ring-1 ring-gray-200">{children}</span>;
}

export default function StudentDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/assignments/my-assignments");
      setPayload(res.data || {});
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const data = useMemo(() => {
    const user = payload?.user || payload?.profile || {};
    const assigned = payload?.assigned_tasks || payload?.assignments || payload?.tasks || [];
    const activities = payload?.activities || [];
    const total = payload?.total_aicte_points ?? payload?.totalAICTEPoints ?? user?.aicte_points ?? 0;
    return {
      user,
      assigned: Array.isArray(assigned) ? assigned : [],
      activities: Array.isArray(activities) ? activities : [],
      totalPoints: Number(total) || 0,
      formula: payload?.formula || payload?.aicte_formula || "AICTE = Σ(Hi × Pi)",
    };
  }, [payload]);

  return (
    <div className="bg-white min-h-screen">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-2xl font-extrabold text-gray-900">Student Dashboard</div>
          <div className="mt-1 text-sm text-gray-700">Track your assignments, skills, and AICTE points.</div>
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
      ) : (
        <>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-[#FACC15] text-gray-900 rounded-xl shadow p-6 border border-yellow-200">
              <div className="text-sm font-semibold">AICTE Points</div>
              <div className="mt-2 text-4xl font-extrabold">{data.totalPoints.toFixed(2)}</div>
            </div>

            <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
              <div className="text-sm font-semibold text-gray-700">Tasks Assigned</div>
              <div className="mt-2 text-3xl font-extrabold text-gray-900">{data.assigned.length}</div>
            </div>

            <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
              <div className="text-sm font-semibold text-gray-700">Skills</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {(Array.isArray(data.user?.skills) ? data.user.skills : []).length > 0 ? (
                  data.user.skills.map((s) => <Tag key={s}>{s}</Tag>)
                ) : (
                  <span className="text-sm text-gray-700">No skills added yet.</span>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-2">
            <Link to="/student/profile" className="bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2">
              Update Profile
            </Link>
            <Link to="/student/tasks" className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2">
              View My Tasks
            </Link>
          </div>

          <div className="mt-8 bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
            <div className="text-lg font-extrabold text-gray-900">Recent Activity Breakdown</div>
            <div className="mt-1 text-sm font-semibold text-gray-700">{data.formula}</div>
            {data.activities.length === 0 ? (
              <div className="mt-3 text-sm text-gray-700">No activities logged yet.</div>
            ) : (
              <div className="mt-4 overflow-x-auto rounded-lg border border-blue-100 bg-white">
                <table className="min-w-full text-sm">
                  <thead className="bg-[#1E3A8A] text-white">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Task</th>
                      <th className="px-4 py-3 text-left font-semibold">Hours</th>
                      <th className="px-4 py-3 text-left font-semibold">Points/Hour</th>
                      <th className="px-4 py-3 text-left font-semibold">Points</th>
                      <th className="px-4 py-3 text-left font-semibold">Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.activities.slice(0, 8).map((a, idx) => (
                      <tr key={a._id || idx} className="border-t border-blue-50">
                        <td className="px-4 py-3 font-semibold text-gray-900">{a.task_title || a.title || "—"}</td>
                        <td className="px-4 py-3 text-gray-900">{Number(a.hours || a.hours_required || 0)}</td>
                        <td className="px-4 py-3 text-gray-900">{Number(a.points_per_hour || 0).toFixed(2)}</td>
                        <td className="px-4 py-3 text-gray-900">{Number(a.points_earned || a.points || 0).toFixed(2)}</td>
                        <td className="px-4 py-3 text-gray-900">{(a.activity_type || "community_service").replaceAll("_", " ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

