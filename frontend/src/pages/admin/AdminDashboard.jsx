import React, { useCallback, useEffect, useMemo, useState } from "react";
import api from "../../api/axios.js";

function UserTable({ title, users, onDelete, busyId }) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
      <div className="text-lg font-extrabold text-gray-900">{title}</div>
      <div className="mt-4 overflow-x-auto rounded-lg border border-blue-100 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-[#1E3A8A] text-white">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Name</th>
              <th className="px-4 py-3 text-left font-semibold">Email</th>
              <th className="px-4 py-3 text-left font-semibold">Role</th>
              <th className="px-4 py-3 text-left font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-gray-600">
                  No accounts yet.
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u._id} className="border-t border-blue-100">
                  <td className="px-4 py-3 font-semibold text-gray-900">{u.name || "—"}</td>
                  <td className="px-4 py-3 text-gray-800">{u.email || "—"}</td>
                  <td className="px-4 py-3 text-gray-800">{u.role || "—"}</td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      disabled={busyId === u._id}
                      onClick={() => onDelete(u)}
                      className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      {busyId === u._id ? "Deleting..." : "Delete"}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [uRes, sRes] = await Promise.all([api.get("/admin/users"), api.get("/admin/stats")]);
      setUsers(Array.isArray(uRes.data) ? uRes.data : []);
      setStats(sRes.data || null);
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to load admin data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const students = useMemo(() => users.filter((u) => u.role === "student"), [users]);
  const ngos = useMemo(() => users.filter((u) => u.role === "ngo"), [users]);
  const admins = useMemo(() => users.filter((u) => u.role === "admin"), [users]);

  const onDelete = async (u) => {
    const ok = window.confirm(`Delete user ${u.email}? This cannot be undone.`);
    if (!ok) return;
    setBusyId(u._id);
    setError("");
    try {
      await api.delete(`/admin/users/${u._id}`);
      await load();
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Delete failed.");
    } finally {
      setBusyId("");
    }
  };

  return (
    <div className="bg-white min-h-screen">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="text-2xl font-extrabold text-gray-900">Administration</div>
          <div className="mt-1 text-sm text-gray-700">Manage NGOs, students, and admins. Use the navbar to open NGO or student tools.</div>
        </div>
        <button
          type="button"
          onClick={load}
          className="rounded-lg bg-[#1E3A8A] px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
        >
          Refresh
        </button>
      </div>

      {error && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {stats && !loading && (
        <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          {[
            ["Users", stats.users_total],
            ["Students", stats.students],
            ["NGOs", stats.ngos],
            ["Tasks", stats.tasks],
          ].map(([k, v]) => (
            <div key={k} className="rounded-xl border border-blue-100 bg-blue-50 p-4 shadow">
              <div className="text-xs font-semibold text-gray-600">{k}</div>
              <div className="mt-1 text-2xl font-extrabold text-gray-900">{v}</div>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="mt-8 text-sm text-gray-700">Loading...</div>
      ) : (
        <div className="mt-8 space-y-8">
          <UserTable title="NGO accounts" users={ngos} onDelete={onDelete} busyId={busyId} />
          <UserTable title="Student accounts" users={students} onDelete={onDelete} busyId={busyId} />
          <UserTable title="Administrator accounts" users={admins} onDelete={onDelete} busyId={busyId} />
        </div>
      )}
    </div>
  );
}
