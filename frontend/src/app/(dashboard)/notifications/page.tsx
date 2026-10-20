"use client";

import { Bell, Loader2 } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import FeedItemRow from "@/features/notifications/components/feed-item-row";
import { useMarkAllRead, useMarkRead, useNotificationFeed, useUnreadCount } from "@/features/notifications/hooks/use-notifications";
import { useTranslation } from "@/lib/i18n/use-translation";

/** All notifications (personal + announcements), 20 per page with "Mehr laden". */
export default function NotificationsPage() {
  const { t } = useTranslation();
  const feed = useNotificationFeed(20);
  const { data: unread = 0 } = useUnreadCount();
  const markRead = useMarkRead();
  const markAll = useMarkAllRead();
  const items = feed.data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <div className="space-y-6">
      <PageHeader icon={Bell} titleKey="notifications.pageTitle" subtitleKey="notifications.pageSubtitle" gradient="from-accent-blue to-brand-600" />
      <section className="mx-auto max-w-3xl rounded-card bg-surface-card p-3 shadow-[var(--shadow-card)] ring-1 ring-surface-border sm:p-5" data-testid="notifications-page">
        <div className="mb-3 flex items-center justify-between px-1">
          <p className="text-sm font-semibold text-text-primary">{t("header.notifications")}</p>
          {unread > 0 && (
            <button type="button" onClick={() => markAll.mutate()} disabled={markAll.isPending} className="text-xs font-semibold text-accent-blue hover:text-accent-blue-hover">
              {t("header.markAllRead")}
            </button>
          )}
        </div>
        {feed.isLoading ? (
          <div className="space-y-2" aria-busy="true">{[0, 1, 2].map((i) => <div key={i} className="h-16 animate-pulse rounded-xl bg-surface-hover" />)}</div>
        ) : feed.isError ? (
          <p className="py-8 text-center text-sm text-text-secondary">
            {t("notifications.loadError")}{" "}
            <button type="button" onClick={() => feed.refetch()} className="font-semibold text-accent-blue hover:underline">{t("notifications.retry")}</button>
          </p>
        ) : items.length === 0 ? (
          <p className="py-10 text-center text-sm text-text-secondary">{t("header.notificationsEmpty")}</p>
        ) : (
          <div className="space-y-1">
            {items.map((item) => <FeedItemRow key={item.id} item={item} full onRead={(id) => markRead.mutate(id)} />)}
          </div>
        )}
        {feed.hasNextPage && (
          <button type="button" onClick={() => feed.fetchNextPage()} disabled={feed.isFetchingNextPage}
                  className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold text-accent-blue ring-1 ring-surface-border hover:bg-surface-hover">
            {feed.isFetchingNextPage && <Loader2 size={14} className="animate-spin" />} {t("notifications.loadMore")}
          </button>
        )}
      </section>
    </div>
  );
}
