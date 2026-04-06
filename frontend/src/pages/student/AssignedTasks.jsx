import React, { useEffect, useMemo, useState } from "react";
import api from "../../api/axios.js";

function StatusBadge({ status }) {
  const s = (status || "assigned").toLowerCase();
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

export default function AssignedTasks() {
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
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to load assignments.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const data = useMemo(() => {
    const assigned = payload?.assigned_tasks || payload?.assignments || payload?.tasks || [];
    const activities = payload?.activities || [];
    const totalPoints = Number(payload?.total_aicte_points ?? payload?.totalAICTEPoints ?? 0) || 0;

    const normalizedAssigned = (Array.isArray(assigned) ? assigned : []).map((x) => x.task || x);
    const normalizedActivities = Array.isArray(activities) ? activities : [];

    const breakdownRows = normalizedActivities.map((a) => {
      const hours = Number(a.hours || a.hours_required || 0) || 0;
      const pph = Number(a.points_per_hour || a.pointsPerHour || 0) || 0;
      const earned = Number(a.points_earned || a.points || hours * pph) || 0;
      return {
        id: a._id,
        title: a.task_title || a.title || "—",
        hours,
        pointsPerHour: pph,
        earned,
      };
    });

    const computedTotal = breakdownRows.reduce((sum, r) => sum + (Number(r.earned) || 0), 0);
    return {
      assigned: normalizedAssigned,
      breakdownRows,
      totalPoints: totalPoints || computedTotal,
      formula: "AICTE = Σ(Hours × Points/Hour)",
    };
  }, [payload]);

  return (
    <div className="bg-white min-h-screen">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-2xl font-extrabold text-gray-900">My Assigned Tasks</div>
          <div className="mt-1 text-sm text-gray-700">View tasks assigned to you and AICTE points earned.</div>
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
          <div className="mt-6 grid grid-cols-1 gap-6">
            {data.assigned.length === 0 ? (
              <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6 text-sm text-gray-700">
                No assigned tasks yet.
              </div>
            ) : (
              data.assigned.map((t) => {
                const urgency = t.urgency ?? t.urgency_norm ?? 0.5;
                const status = t.status || "assigned";
                const hours = Number(t.hours_required || 0) || 0;
                const pph = Number(t.points_per_hour || 0) || 0;
                const points = hours * pph;
                return (
                  <div key={t._id} className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                      <div>
                        <div className="text-lg font-extrabold text-gray-900">{t.title}</div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <UrgencyBadge urgency01={urgency} />
                          <StatusBadge status={status} />
                        </div>
                      </div>
                      <div className="text-sm text-gray-700">
                        <div>
                          <span className="font-semibold text-gray-900">Hours Required:</span> {hours}
                        </div>
                        <div className="mt-1">
                          <span className="font-semibold text-gray-900">Points to Earn:</span> {points.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="mt-10 bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
            <div className="text-lg font-extrabold text-gray-900">AICTE Breakdown</div>
            <div className="mt-1 text-sm text-gray-700">{data.formula}</div>

            {data.breakdownRows.length === 0 ? (
              <div className="mt-4 text-sm text-gray-700">No completed activities yet.</div>
            ) : (
              <div className="mt-4 overflow-x-auto rounded-lg border border-blue-100 bg-white">
                <table className="min-w-full text-sm">
                  <thead className="bg-[#1E3A8A] text-white">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Task</th>
                      <th className="px-4 py-3 text-left font-semibold">Hours</th>
                      <th className="px-4 py-3 text-left font-semibold">Points/Hour</th>
                      <th className="px-4 py-3 text-left font-semibold">Points Earned</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.breakdownRows.map((r, idx) => (
                      <tr key={r.id || idx} className="border-t border-blue-50">
                        <td className="px-4 py-3 font-semibold text-gray-900">{r.title}</td>
                        <td className="px-4 py-3 text-gray-900">{r.hours}</td>
                        <td className="px-4 py-3 text-gray-900">{r.pointsPerHour.toFixed(2)}</td>
                        <td className="px-4 py-3 font-extrabold text-gray-900">{r.earned.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mt-6 bg-[#FACC15] text-gray-900 rounded-xl shadow p-6 border border-yellow-200">
              <div className="text-sm font-semibold">Total AICTE Points</div>
              <div className="mt-2 text-4xl font-extrabold">{data.totalPoints.toFixed(2)}</div>
              <div className="mt-2 text-sm font-semibold text-gray-800">{data.formula}</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

