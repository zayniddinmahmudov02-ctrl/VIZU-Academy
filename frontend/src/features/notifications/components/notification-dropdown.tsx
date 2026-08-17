"use client";

import { useState } from "react";
import {
  Bell,
  BookOpen,
  GraduationCap,
  Info,
  Loader2,
  Play,
  Settings as SettingsIcon,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import Popover from "@/components/ui/popover";
import { api } from "@/services/api";
import { useTranslation } from "@/lib/i18n/use-translation";
import { useNotifications } from "../hooks/use-notifications";
import { formatRelativeTime } from "../utils/format-relative-time";
import type { Notification, NotificationType } from "../types/notification";

const TYPE_ICON: Record<NotificationType, LucideIcon> = {
  information: Info,
  update: Sparkles,
  exam: GraduationCap,
  course: BookOpen,
  system: SettingsIcon,
};

const TYPE_ACCENT: Record<NotificationType, string> = {
  information: "bg-accent-blue/10 text-accent-blue",
  update: "bg-accent-purple/10 text-accent-purple",
  exam: "bg-warning/10 text-warning",
  course: "bg-success/10 text-success",
  system: "bg-text-muted/10 text-text-muted",
};

export default function NotificationDropdown() {
  const { t } = useTranslation();
  const { notifications, unreadCount, loading, markRead, markAllRead } = useNotifications();

  return (
    <Popover
      trigger={
        <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-surface-card text-text-secondary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:text-accent-blue">
          <Bell size={15} />
          {unreadCount > 0 && (
            <span className="absolute right-2 top-2 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[9px] font-bold text-white ring-2 ring-surface-card">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </span>
      }
    >
      <div className="flex items-center justify-between px-1">
        <p className="text-sm font-semibold text-text-primary">{t("header.notifications")}</p>
        {unreadCount > 0 && (
          <button
            type="button"
            onClick={markAllRead}
            className="text-xs font-semibold text-accent-blue transition-colors hover:text-accent-blue-hover"
          >
            {t("header.markAllRead")}
          </button>
        )}
      </div>

      <div className="mt-2 max-h-80 space-y-1 overflow-y-auto">
        {loading ? (
          <p className="px-1 py-6 text-center text-sm text-text-secondary">
            {t("common.loading")}
          </p>
        ) : notifications.length === 0 ? (
          <p className="px-1 py-6 text-center text-sm text-text-secondary">
            {t("header.notificationsEmpty")}
          </p>
        ) : (
          notifications.map((notification) => (
            <NotificationRow
              key={notification.id}
              notification={notification}
              onRead={() => markRead(notification.id)}
            />
          ))
        )}
      </div>
    </Popover>
  );
}

function NotificationRow({
  notification,
  onRead,
}: {
  notification: Notification;
  onRead: () => void;
}) {
  const { t } = useTranslation();
  const Icon = TYPE_ICON[notification.type];

  return (
    <button
      type="button"
      onClick={() => !notification.isRead && onRead()}
      aria-label={notification.isRead ? undefined : t("header.markRead")}
      className={`flex w-full items-start gap-3 rounded-xl px-2 py-2.5 text-left transition-colors hover:bg-surface-hover ${
        notification.isRead ? "" : "bg-accent-blue/5"
      }`}
    >
      <span
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${TYPE_ACCENT[notification.type]}`}
      >
        <Icon size={15} />
      </span>

      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5">
          <span className="truncate text-sm font-semibold text-text-primary">
            {notification.title}
          </span>
          {!notification.isRead && (
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent-blue" />
          )}
        </span>
        <span className="mt-0.5 block line-clamp-2 text-xs text-text-secondary">
          {notification.message}
        </span>
        <span className="mt-1 flex items-center gap-2 text-[11px] text-text-muted">
          {formatRelativeTime(notification.createdAt, t)}
          {notification.audioUrl && <AudioFeedbackButton audioUrl={notification.audioUrl} />}
        </span>
      </span>
    </button>
  );
}

function AudioFeedbackButton({ audioUrl }: { audioUrl: string }) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);

  async function play(event: React.MouseEvent) {
    event.stopPropagation();
    if (loading) return;

    setLoading(true);
    try {
      const response = await api.get(audioUrl, { responseType: "blob" });
      const url = URL.createObjectURL(response.data);
      const audio = new Audio(url);
      audio.addEventListener("ended", () => URL.revokeObjectURL(url));
      await audio.play();
    } catch {
      // Playback failure isn't worth surfacing an error state for a
      // small inline dropdown control — the notification text stands on its own.
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={play}
      disabled={loading}
      className="flex items-center gap-1 font-semibold text-accent-blue transition-colors hover:text-accent-blue-hover disabled:opacity-60"
    >
      {loading ? <Loader2 size={11} className="animate-spin" /> : <Play size={11} />}
      {t("header.playFeedback")}
    </button>
  );
}
