"use client";

import { useCallback, useEffect, useState } from "react";

import { NOTIFICATIONS_API_ENABLED } from "@/constants/feature-flags";
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../services/notification-service";
import type { Notification } from "../types/notification";

interface UseNotificationsResult {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;
  markRead: (notificationId: string) => Promise<void>;
  markAllRead: () => Promise<void>;
}

export function useNotifications(): UseNotificationsResult {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const load = useCallback(async () => {
    if (!NOTIFICATIONS_API_ENABLED) {
      setNotifications([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await getNotifications();
      setNotifications([...data].sort((a, b) => b.createdAt.localeCompare(a.createdAt)));
    } catch (err) {
      // Backend not deployed yet or genuinely no notifications — either way,
      // the dropdown just shows its empty state rather than an error.
      console.warn("Failed to load notifications:", err);
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function markRead(notificationId: string) {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, isRead: true } : n)),
    );

    try {
      await markNotificationRead(notificationId);
    } catch (err) {
      console.warn("Failed to mark notification as read:", err);
    }
  }

  async function markAllRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));

    try {
      await markAllNotificationsRead();
    } catch (err) {
      console.warn("Failed to mark all notifications as read:", err);
    }
  }

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return { notifications, unreadCount, loading, markRead, markAllRead };
}
