import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { apiFetch } from "@/services/api";

export type UserRole = "citizen" | "officer" | "admin";

const ROLE_OVERRIDE_STORAGE_KEY = "selected_login_role";

interface RoleContextType {
  role: UserRole;
  setRole: (role: UserRole) => void;
  userName: string;
  userId: string | null;
  isLoggedIn: boolean;
  isAuthLoading: boolean;
  login: (email: string, password: string, selectedRole: UserRole) => Promise<void>;
  register: (email: string, password: string, role: UserRole) => Promise<{ emailConfirmationRequired: boolean }>;
  logout: () => Promise<void>;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<UserRole>("citizen");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [userName, setUserName] = useState("Корисник");
  const [userId, setUserId] = useState<string | null>(null);

  const getRoleFromSession = (session: Session): UserRole => {
    const raw =
      session.user.app_metadata?.app_role ??
      session.user.user_metadata?.app_role ??
      session.user.user_metadata?.role;

    if (raw === "admin" || raw === "officer" || raw === "citizen") {
      return raw;
    }

    return "citizen";
  };

  const displayNameFromEmail = (email?: string | null): string => {
    if (!email) return "Корисник";
    return email.split("@")[0] || "Корисник";
  };

  const getStoredRoleOverride = (): UserRole | null => {
    const raw = localStorage.getItem(ROLE_OVERRIDE_STORAGE_KEY);
    if (raw === "citizen" || raw === "officer" || raw === "admin") {
      return raw;
    }
    return null;
  };

  const setRoleOverride = (selectedRole: UserRole) => {
    localStorage.setItem(ROLE_OVERRIDE_STORAGE_KEY, selectedRole);
  };

  const clearRoleOverride = () => {
    localStorage.removeItem(ROLE_OVERRIDE_STORAGE_KEY);
  };

  const syncSession = async (session: Session | null) => {
    if (!session) {
      localStorage.removeItem("auth_token");
      clearRoleOverride();
      setIsLoggedIn(false);
      setRole("citizen");
      setUserName("Корисник");
      setUserId(null);
      return;
    }

    localStorage.setItem("auth_token", session.access_token);
    setIsLoggedIn(true);
    setUserId(session.user.id);
    const roleOverride = getStoredRoleOverride();
    const sessionUserName = displayNameFromEmail(session.user.email);
    setRole(roleOverride ?? getRoleFromSession(session));
    setUserName(sessionUserName);

    try {
      const me = await apiFetch<{ id: string; email: string | null; role: UserRole }>("/users/me");
      if (roleOverride && roleOverride !== me.role) {
        await apiFetch("/users/me/role", {
          method: "PATCH",
          body: JSON.stringify({ role: roleOverride }),
        });
      }
      setRole(roleOverride ?? me.role);
      setUserName(session.user.email ? sessionUserName : displayNameFromEmail(me.email));
      setUserId(me.id);
    } catch {
      // Keep session-derived role/email if backend profile sync is not yet available.
    }
  };

  useEffect(() => {
    let isMounted = true;

    const init = async () => {
      try {
        const { data, error } = await supabase.auth.getSession();
        if (error) throw error;
        if (isMounted) {
          await syncSession(data.session);
        }
      } finally {
        if (isMounted) {
          setIsAuthLoading(false);
        }
      }
    };

    void init();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      void syncSession(session);
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string, selectedRole: UserRole) => {
    setRoleOverride(selectedRole);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      clearRoleOverride();
      throw error;
    }
  };

  const register = async (email: string, password: string, selectedRole: UserRole) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { app_role: selectedRole },
      },
    });

    if (error) throw error;

    return {
      emailConfirmationRequired: !data.session,
    };
  };

  const logout = async () => {
    await supabase.auth.signOut();
    localStorage.removeItem("auth_token");
    clearRoleOverride();
    setIsLoggedIn(false);
    setRole("citizen");
    setUserName("Корисник");
    setUserId(null);
  };

  const contextValue = useMemo(
    () => ({ role, setRole, userName, userId, isLoggedIn, isAuthLoading, login, register, logout }),
    [role, userName, userId, isLoggedIn, isAuthLoading],
  );

  return (
    <RoleContext.Provider value={contextValue}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) throw new Error("useRole must be used within RoleProvider");
  return context;
}
