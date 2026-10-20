"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { NOTIFICATIONS_API_ENABLED } from "@/constants/feature-flags";
import { getNotificationFeed, getUnreadCount, markFeedAllRead, markFeedItemRead } from "../services/notification-service";
import type { FeedPage } from "../types/notification";

export const notificationKeys = {
  unread: ["notifications", "unread"] as const,
  feed: (limit: number) => ["notifications", "feed", limit] as const,
};

/** Badge count — one cheap COUNT request, refreshed when the window regains
 * focus or after reading; no interval polling. */
export function useUnreadCount() {
  return useQuery({
    queryKey: notificationKeys.unread,
    queryFn: getUnreadCount,
    enabled: NOTIFICATIONS_API_ENABLED,
    staleTime: 60_000,
    retry: false,
  });
}

/** Feed pages (cursor paging). `enabled` lets the bell load only when opened. */
export function useNotificationFeed(limit = 20, enabled = true) {
  return useInfiniteQuery({
    queryKey: notificationKeys.feed(limit),
    queryFn: ({ pageParam }) => getNotificationFeed(pageParam, limit),
    initialPageParam: null as string | null,
    getNextPageParam: (last: FeedPage) => last.next_before,
    enabled: NOTIFICATIONS_API_ENABLED && enabled,
    staleTime: 30_000,
    retry: false,
  });
}

function setRead(qc: ReturnType<typeof useQueryClient>, id: string | null) {
  qc.setQueriesData<{ pages: FeedPage[]; pageParams: unknown[] }>({ queryKey: ["notifications", "feed"] }, (old) =>
    old ? { ...old, pages: old.pages.map((p) => ({ ...p, items: p.items.map((i) => (id === null || i.id === id ? { ...i, is_read: true } : i)) })) } : old,
  );
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => markFeedItemRead(id),
    onMutate: (id) => setRead(qc, id),
    onSuccess: (unread) => qc.setQueryData(notificationKeys.unread, unread),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: markFeedAllRead,
    onMutate: () => {
      setRead(qc, null);
      qc.setQueryData(notificationKeys.unread, 0);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: notificationKeys.unread }),
  });
}
