"use client";

import { useState } from "react";
import Link from "next/link";
import { Bell } from "lucide-react";

import Popover from "@/components/ui/popover";
import { useTranslation } from "@/lib/i18n/use-translation";
import { useMarkAllRead, useMarkRead, useNotificationFeed, useUnreadCount } from "../hooks/use-notifications";
import FeedItemRow from "./feed-item-row";

/** Header bell: badge from GET /notifications/unread-count; the latest 10
 * items load only when the bell is opened. */
export default function NotificationDropdown() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const { data: unread = 0 } = useUnreadCount();
  const feed = useNotificationFeed(10, open);
  const markRead = useMarkRead();
  const markAll = useMarkAllRead();
  const items = feed.data?.pages[0]?.items ?? [];

  return (
    <Popover
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (o && feed.data) feed.refetch(); // first open loads via `enabled`; later opens refresh
      }}
      triggerLabel={t("notifications.bellAria", { n: unread })}
      trigger={
        <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-surface-card text-text-secondary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:text-accent-blue">
          <Bell size={15} aria-hidden="true" />
          {unread > 0 && (
            <span className="absolute right-2 top-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-0.5 text-[9px] font-bold text-white ring-2 ring-surface-card" data-testid="notification-badge">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </span>
      }
    >
      <div className="flex items-center justify-between px-1">
        <p className="text-sm font-semibold text-text-primary">{t("header.notifications")}</p>
        {unread > 0 && (
          <button type="button" onClick={() => markAll.mutate()} disabled={markAll.isPending}
                  className="text-xs font-semibold text-accent-blue transition-colors hover:text-accent-blue-hover">
            {t("header.markAllRead")}
          </button>
        )}
      </div>

      <div className="mt-2 max-h-80 space-y-1 overflow-y-auto">
        {feed.isLoading ? (
          <p className="px-1 py-6 text-center text-sm text-text-secondary">{t("common.loading")}</p>
        ) : feed.isError ? (
          <p className="px-1 py-6 text-center text-sm text-text-secondary">{t("notifications.loadError")}</p>
        ) : items.length === 0 ? (
          <p className="px-1 py-6 text-center text-sm text-text-secondary">{t("header.notificationsEmpty")}</p>
        ) : (
          items.map((item) => <FeedItemRow key={item.id} item={item} onRead={(id) => markRead.mutate(id)} onNavigate={() => setOpen(false)} />)
        )}
      </div>

      <Link href="/notifications" prefetch={false} onClick={() => setOpen(false)}
            className="mt-2 block rounded-xl py-2 text-center text-xs font-semibold text-accent-blue hover:bg-surface-hover">
        {t("header.viewAllNotifications")}
      </Link>
    </Popover>
  );
}
