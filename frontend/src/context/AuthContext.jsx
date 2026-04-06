import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token") || "");
  const [role, setRole] = useState(() => localStorage.getItem("role") || "");
  const [user, setUser] = useState(() => {
    const userId = localStorage.getItem("userId") || "";
    const name = localStorage.getItem("name") || "";
    return userId || name ? { userId, name } : null;
  });

  const login = (newToken, newRole, userId, name) => {
    localStorage.setItem("token", newToken);
    localStorage.setItem("role", newRole);
    localStorage.setItem("userId", userId);
    localStorage.setItem("name", name || "");

    setToken(newToken);
    setRole(newRole);
    setUser({ userId, name: name || "" });
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("userId");
    localStorage.removeItem("name");

    setToken("");
    setRole("");
    setUser(null);
  };

  const isAuthenticated = () => Boolean(localStorage.getItem("token"));

  useEffect(() => {
    // Keep state in sync if storage changes in another tab
    const onStorage = (e) => {
      if (!["token", "role", "userId", "name"].includes(e.key)) return;
      setToken(localStorage.getItem("token") || "");
      setRole(localStorage.getItem("role") || "");
      const userId = localStorage.getItem("userId") || "";
      const name = localStorage.getItem("name") || "";
      setUser(userId || name ? { userId, name } : null);
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const value = useMemo(
    () => ({ user, role, token, login, logout, isAuthenticated }),
    [user, role, token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

