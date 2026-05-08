import {
  Home,
  FileText,
  PlusCircle,
  LayoutDashboard,
  ClipboardList,
  BarChart3,
  Settings,
  Map as MapIcon,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useRole } from "@/context/RoleContext";
import { Sidebar, SidebarContent } from "@/components/ui/sidebar";

interface NavItem {
  title: string;
  url: string;
  icon: React.ElementType;
}

const citizenNav: NavItem[] = [
  { title: "Почетна", url: "/", icon: Home },
  { title: "Интерактивна мапа", url: "/public-map", icon: MapIcon },
  { title: "Мои пријави", url: "/my-complaints", icon: FileText },
  { title: "Нова пријава", url: "/new-complaint", icon: PlusCircle },
  { title: "Поставки", url: "/settings", icon: Settings },
];

const officerNav: NavItem[] = [
  { title: "Контролна табла", url: "/dashboard", icon: LayoutDashboard },
  { title: "Интерактивна мапа", url: "/public-map", icon: MapIcon },
  { title: "Доделени пријави", url: "/assigned-complaints", icon: ClipboardList },
  { title: "Аналитички преглед", url: "/analytics", icon: BarChart3 },
  { title: "Поставки", url: "/settings", icon: Settings },
];

const adminNav: NavItem[] = [
  { title: "Контролна табла", url: "/dashboard", icon: LayoutDashboard },
  { title: "Интерактивна мапа", url: "/public-map", icon: MapIcon },
  { title: "Управување со пријави", url: "/manage-complaints", icon: ClipboardList },
  { title: "Аналитички преглед", url: "/analytics", icon: BarChart3 },
  { title: "Поставки", url: "/settings", icon: Settings },
];

export function AppSidebar() {
  const { role } = useRole();

  const navItems =
    role === "citizen" ? citizenNav :
    role === "officer" ? officerNav :
    adminNav;

  return (
    <Sidebar collapsible="offcanvas">
      <SidebarContent>
        <div className="px-3 py-4">
          <p className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Мени
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.url}
                to={item.url}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-foreground hover:bg-accent hover:text-accent-foreground"
                  }`
                }
              >
                <item.icon className="h-4 w-4 shrink-0" />
                <span>{item.title}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </SidebarContent>
    </Sidebar>
  );
}
