import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../../api/axios.js";
import { useAuth } from "../../context/AuthContext.jsx";

export default function AdminLogin() {
  const navigate = useNavigate();
  const auth = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/auth/login", { email, password });
      const token = res.data?.token || res.data?.access_token || "";
      const role = res.data?.role || "";
      const userId = res.data?.user_id || res.data?.userId || "";
      const name = res.data?.name || "Admin";

      if (role !== "admin") {
        setError("This account is not an administrator.");
        return;
      }
      if (token) auth.login(token, role, userId, name);
      navigate("/admin/dashboard", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white min-h-screen">
      <div className="max-w-xl mx-auto bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
        <div className="text-2xl font-extrabold text-gray-900">Administrator Login</div>
        <p className="mt-2 text-sm text-gray-700">Sign in with an admin account.</p>

        {error && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="text-sm font-semibold text-gray-900">Email</label>
            <input
              type="email"
              className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="admin@example.com"
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-900">Password</label>
            <input
              type="password"
              className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>

          <div className="flex items-center justify-between gap-3">
            <button
              disabled={loading}
              className="bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2 disabled:opacity-60"
              type="submit"
            >
              {loading ? "Signing in..." : "Login"}
            </button>
            <Link to="/admin/register" className="text-sm font-semibold text-blue-700 hover:underline">
              Create admin account
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
