import { apiFetch } from "./api";

export interface NotificationRead {
  id: number;
  user_id: string;
  report_id: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export function fetchNotifications(): Promise<NotificationRead[]> {
  return apiFetch<NotificationRead[]>("/notifications");
}

export function fetchUnreadCount(): Promise<{ count: number }> {
  return apiFetch<{ count: number }>("/notifications/unread-count");
}

export function markNotificationRead(id: number): Promise<NotificationRead> {
  return apiFetch<NotificationRead>(`/notifications/${id}/read`, { method: "PATCH" });
}

export function markAllRead(): Promise<{ marked_read: number }> {
  return apiFetch<{ marked_read: number }>("/notifications/read-all", { method: "PATCH" });
}
