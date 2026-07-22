import { api } from "@/services/api";

import type { Notification, NotificationInput } from "../types/notification";

export async function getNotifications() {
  const response = await api.get<Notification[]>("/notifications");
  return response.data;
}

export async function markNotificationRead(notificationId: string) {
  const response = await api.patch<Notification>(`/notifications/${notificationId}/read`);
  return response.data;
}

export async function markAllNotificationsRead() {
  await api.post("/notifications/read-all");
}

export async function createNotification(payload: NotificationInput) {
  const response = await api.post<Notification>("/notifications", payload);
  return response.data;
}
