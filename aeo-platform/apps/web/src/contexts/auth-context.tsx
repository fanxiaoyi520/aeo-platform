"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { AuthUser } from "@/lib/types";

type AuthState = {
  user: AuthUser | null;
  loading: boolean;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  logout: async () => {},
  refresh: async () => {},
});

export function useAuth(): AuthState {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/me");
      if (!res.ok) {
        setUser(null);
        return;
      }
      const json = (await res.json()) as {
        data: { user_id: string; tenant_id: string; role: string; email: string };
      };
      setUser({
        id: json.data.user_id,
        email: json.data.email,
        display_name: "",
        role: json.data.role,
        tenant_id: json.data.tenant_id,
      });
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    window.location.href = "/login";
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <AuthContext.Provider value={{ user, loading, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}
