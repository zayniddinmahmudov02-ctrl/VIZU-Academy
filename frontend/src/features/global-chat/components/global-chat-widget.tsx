"use client";

import { useCallback, useEffect, useState } from "react";
import { MessagesSquare } from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useTranslation } from "@/lib/i18n/use-translation";
import { getUnreadCount } from "../global-chat-service";
import ChatPanel from "./chat-panel";

const UNREAD_POLL_MS = 30_000;

/** Floating Global Chat button (bottom right) for every logged-in user on
 *  the student, teacher and admin dashboards. While closed it only polls the
 *  unread count (twice a minute, visible tabs only); the chat itself is
 *  mounted when opened. */
export default function GlobalChatWidget() {
  const { t } = useTranslation();
  const { user } = useCurrentUser();
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const loggedIn = !!user;

  useEffect(() => {
    if (!loggedIn || open) return;
    let alive = true;
    const load = () => {
      if (document.visibilityState !== "visible") return;
      getUnreadCount().then((n) => alive && setUnread(n)).catch(() => undefined);
    };
    load();
    const timer = setInterval(load, UNREAD_POLL_MS);
    document.addEventListener("visibilitychange", load);
    return () => {
      alive = false;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", load);
    };
  }, [loggedIn, open]);

  const close = useCallback(() => setOpen(false), []);
  const onUnread = useCallback((n: number) => setUnread(n), []);

  if (!user) return null;

  const label = unread > 0 ? `${t("globalChat.open")} – ${t("globalChat.unread", { n: unread })}` : t("globalChat.open");

  return (
    <>
      {!open && (
        <button type="button" onClick={() => setOpen(true)} aria-label={label} title={t("globalChat.title")} data-testid="global-chat-button"
                className="fixed right-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-accent-blue text-white shadow-[var(--shadow-lg)] ring-4 ring-surface-bg transition-transform hover:scale-105 focus-visible:outline-none focus-visible:ring-accent-blue/40 sm:right-6"
                style={{ bottom: "calc(1rem + env(safe-area-inset-bottom))" }}>
          <MessagesSquare size={24} aria-hidden="true" />
          {unread > 0 && (
            <span data-testid="global-chat-badge"
                  className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-danger px-1 text-[11px] font-bold leading-none text-white ring-2 ring-surface-bg">
              {unread > 99 ? "99+" : unread}
            </span>
          )}
        </button>
      )}
      {open && <ChatPanel onClose={close} onUnread={onUnread} isSuperAdmin={user.role === "SUPER_ADMIN"} />}
    </>
  );
}
