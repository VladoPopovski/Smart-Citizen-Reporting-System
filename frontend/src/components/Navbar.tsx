import { Bell, LogOut, CheckCheck } from "lucide-react";
import { useRole } from "@/context/RoleContext";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useNavigate } from "react-router-dom";
import logo from "@/assets/Urban.png";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchNotifications, markAllRead, markNotificationRead } from "@/services/notifications";

export function Navbar() {
  const { role, userName, logout } = useRole();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const avatarInitial = userName.trim().charAt(0).toUpperCase() || "К";

  const roleLabels: Record<string, string> = {
    citizen: "Корисник",
    officer: "Службеник",
    admin: "Администратор",
  };

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: fetchNotifications,
    refetchInterval: 30000,
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markAllMutation = useMutation({
    mutationFn: markAllRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markOneMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("mk-MK", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  return (
    <header className="h-16 border-b bg-card flex items-center justify-between px-4 md:px-6 sticky top-0 z-50">
      <div className="flex items-center gap-2">
        <SidebarTrigger />
        <img src={logo} className="h-10 md:h-14 w-auto" alt="UrbanCare Logo" />
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        <span className="hidden sm:inline-block text-xs font-medium text-muted-foreground bg-secondary px-3 py-1.5 rounded-md">
          {roleLabels[role]}
        </span>

        <Popover>
          <PopoverTrigger asChild>
            <button className="p-2 rounded-lg hover:bg-secondary transition-colors relative" aria-label="Известувања">
              <Bell className="h-5 w-5 text-muted-foreground" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 min-w-[16px] h-4 bg-primary text-primary-foreground text-[10px] font-bold rounded-full flex items-center justify-center px-0.5">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-80 p-0">
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <span className="font-semibold text-sm">Известувања</span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllMutation.mutate()}
                  className="flex items-center gap-1 text-xs text-primary hover:underline"
                >
                  <CheckCheck className="h-3.5 w-3.5" />
                  Означи сите прочитани
                </button>
              )}
            </div>

            <div className="max-h-80 overflow-y-auto divide-y">
              {notifications.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">Нема известувања.</p>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    onClick={() => { if (!n.is_read) markOneMutation.mutate(n.id); }}
                    className={`px-4 py-3 cursor-pointer hover:bg-secondary/50 transition-colors ${!n.is_read ? "bg-primary/5" : ""}`}
                  >
                    <div className="flex items-start gap-2">
                      {!n.is_read && <span className="mt-1.5 w-2 h-2 rounded-full bg-primary shrink-0" />}
                      <div className={!n.is_read ? "" : "ml-4"}>
                        <p className="text-sm leading-snug">{n.message}</p>
                        <p className="text-xs text-muted-foreground mt-1">{formatDate(n.created_at)}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </PopoverContent>
        </Popover>

        <Avatar className="h-8 w-8 md:h-9 md:w-9">
          <AvatarFallback className="bg-primary/10 text-primary font-semibold text-sm">
            {avatarInitial}
          </AvatarFallback>
        </Avatar>
        <Button variant="ghost" size="sm" onClick={handleLogout} className="text-destructive hover:text-destructive p-2 md:px-3">
          <LogOut className="h-4 w-4 md:mr-1" />
          <span className="hidden md:inline">Одјава</span>
        </Button>
      </div>
    </header>
  );
}
