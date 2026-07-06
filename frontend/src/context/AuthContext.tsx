import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "@/api/endpoints";
import { clearTokens, getAccessToken, setTokens } from "@/api/client";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (payload: { username: string; password: string; full_name: string; email?: string; role: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      return;
    }
    try {
      const { data } = await authApi.me();
      setUser(data);
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  const login = useCallback(async (username: string, password: string) => {
    const { data } = await authApi.login(username, password);
    setTokens(data.access_token, data.refresh_token);
    setUser(data.user);
  }, []);

  const register = useCallback(async (payload: { username: string; password: string; full_name: string; email?: string; role: string }) => {
    await authApi.register(payload);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore
    }
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, register, logout, refreshUser }), [user, loading, login, register, logout, refreshUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
