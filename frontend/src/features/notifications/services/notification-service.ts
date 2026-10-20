import { api } from "@/services/api";

import type { FeedPage, Notification, NotificationInput } from "../types/notification";

// The shared axios client's baseURL is the bare backend origin — every
// call site must include /api/v1 itself (see ADMIN_ENDPOINTS for the
// same convention). The public nginx gateway only proxies /api/v1/*,
// so a bare path here 404s in production even though the backend route
// itself exists and is correctly mounted.
export async function getNotifications() {
  const response = await api.get<Notification[]>("/api/v1/notifications");
  return response.data;
}

/** Personal notifications + admin broadcasts, newest first, one page. */
export async function getNotificationFeed(before?: string | null, limit = 20): Promise<FeedPage> {
  const params: Record<string, string | number> = { limit };
  if (before) params.before = before;
  const data = (await api.get<FeedPage>("/api/v1/notifications/feed", { params })).data;
  return { items: Array.isArray(data?.items) ? data.items : [], next_before: data?.next_before ?? null };
}

export async function getUnreadCount(): Promise<number> {
  return (await api.get<{ unread: number }>("/api/v1/notifications/unread-count")).data?.unread ?? 0;
}

export async function markFeedItemRead(itemId: string): Promise<number> {
  return (await api.post<{ unread: number }>(`/api/v1/notifications/feed/${encodeURIComponent(itemId)}/read`)).data?.unread ?? 0;
}

export async function markFeedAllRead(): Promise<void> {
  await api.post("/api/v1/notifications/feed/read-all");
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
