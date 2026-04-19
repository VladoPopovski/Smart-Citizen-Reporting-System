import { createContext, useContext, useState, ReactNode } from "react";

export type UserRole = "citizen" | "officer" | "admin";

interface RoleContextType {
  role: UserRole;
  setRole: (role: UserRole) => void;
  userName: string;
  isLoggedIn: boolean;
  login: (role: UserRole) => void;
  logout: () => void;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<UserRole>("citizen");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const userName =
    role === "citizen" ? "Марко Петров" :
    role === "officer" ? "Ана Стојанова" :
    "Админ Корисник";

  const login = (selectedRole: UserRole) => {
    setRole(selectedRole);
    setIsLoggedIn(true);
  };

  const logout = () => {
    setIsLoggedIn(false);
    setRole("citizen");
  };

  return (
    <RoleContext.Provider value={{ role, setRole, userName, isLoggedIn, login, logout }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) throw new Error("useRole must be used within RoleProvider");
  return context;
}
