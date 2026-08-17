import { api } from "@/services/api";

import type { Notification, NotificationInput } from "../types/notification";

// The shared axios client's baseURL is the bare backend origin — every
// call site must include /api/v1 itself (see ADMIN_ENDPOINTS for the
// same convention). The public nginx gateway only proxies /api/v1/*,
// so a bare path here 404s in production even though the backend route
// itself exists and is correctly mounted.
export async function getNotifications() {
  const response = await api.get<Notification[]>("/api/v1/notifications");
  return response.data;
}

export async function markNotificationRead(notificationId: string) {
  const response = await api.patch<Notification>(`/api/v1/notifications/${notificationId}/read`);
  return response.data;
}

export async function markAllNotificationsRead() {
  await api.post("/api/v1/notifications/read-all");
}

export async function createNotification(payload: NotificationInput) {
  const response = await api.post<Notification>("/api/v1/notifications", payload);
  return response.data;
}
