"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDown, Ban, Check, ChevronDown, Eye, EyeOff, Loader2, MessagesSquare, Pin, PinOff, Send, ShieldAlert, VolumeX, WifiOff, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import {
  MAX_LENGTH,
  canDeleteOwn,
  canEditOwn,
  deleteMessage,
  editMessage,
  errorCode,
  fmtDateTime,
  fmtMessageTime,
  getHistory,
  getUpdates,
  markRead,
  moderateMessage,
  sendMessage,
  type ChatMessage,
  type HistoryPage,
  type RestrictionKind,
  type ViewerStatus,
} from "../global-chat-service";
import { ConfirmDeleteDialog, EditMessageForm, OwnMessageMenu } from "./own-message-actions";
import RestrictDialog from "./restrict-dialog";

const POLL_MS = 4000;
const NEAR_BOTTOM_PX = 80;
const NEAR_TOP_PX = 80;

function sortMessages(list: ChatMessage[]): ChatMessage[] {
  return list.sort((a, b) => a.created_at.localeCompare(b.created_at) || a.id.localeCompare(b.id));
}

function merge(current: ChatMessage[], incoming: ChatMessage[]): ChatMessage[] {
  const byId = new Map(current.map((m) => [m.id, m]));
  for (const m of incoming) byId.set(m.id, m);
  return sortMessages([...byId.values()]);
}

/** The Global Chat window: newest page first, older pages when scrolled to
 *  the top, new/changed messages by polling /updates. Message text is
 *  rendered as React text (never as HTML). Moderation buttons only appear
 *  for moderators, Edit / Delete ("…" menu) only on the caller's own
 *  messages — the server checks every action again. */
export default function ChatPanel({ onClose, onUnread, isSuperAdmin }: { onClose: () => void; onUnread: (n: number) => void; isSuperAdmin: boolean }) {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pinned, setPinned] = useState<ChatMessage[]>([]);
  const [pinsOpen, setPinsOpen] = useState(false);
  const [me, setMe] = useState<ViewerStatus | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [atBottom, setAtBottom] = useState(true);
  const [newBelow, setNewBelow] = useState(0);
  const [online, setOnline] = useState(() => typeof navigator === "undefined" || navigator.onLine);
  const [pollFailures, setPollFailures] = useState(0);
  const [restrict, setRestrict] = useState<{ user: { id: string; name: string }; messageId: string; kind: RestrictionKind } | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<ChatMessage | null>(null);

  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const syncRef = useRef<string | null>(null);
  const atBottomRef = useRef(true);
  const messagesRef = useRef<ChatMessage[]>([]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const errorText = useCallback((err: unknown) => {
    const code = errorCode(err);
    if (!code && !(err as { response?: unknown })?.response) return t("globalChat.err_network");
    const key = `globalChat.err_${code}`;
    const text = code ? t(key) : key;
    return text !== key ? text : t("globalChat.err_generic");
  }, [t]);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      const el = listRef.current;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }, []);

  const readUpTo = useCallback((list: ChatMessage[]) => {
    const last = [...list].reverse().find((m) => m.status === "visible");
    setNewBelow(0);
    onUnread(0);
    markRead(last?.id).catch(() => undefined);
  }, [onUnread]);

  const applyLatest = useCallback((page: HistoryPage) => {
    setMessages(sortMessages(page.items));
    setPinned(page.pinned);
    setMe(page.me);
    setHasMore(page.has_more);
    syncRef.current = page.sync;
    setLoaded(true);
    setLoadError(false);
    scrollToBottom();
    readUpTo(page.items);
  }, [readUpTo, scrollToBottom]);

  const loadLatest = useCallback(() => getHistory().then(applyLatest), [applyLatest]);

  // first page
  useEffect(() => {
    getHistory().then(applyLatest).catch(() => setLoadError(true));
  }, [applyLatest]);

  // online / offline
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  // polling while the window is open and the tab visible
  useEffect(() => {
    if (!loaded) return;
    let busy = false;
    const tick = async () => {
      if (busy || document.visibilityState !== "visible" || !navigator.onLine || !syncRef.current) return;
      busy = true;
      try {
        const upd = await getUpdates(syncRef.current);
        setPollFailures(0);
        if (upd.reset) {
          await loadLatest();
          return;
        }
        syncRef.current = upd.sync;
        setPinned(upd.pinned);
        setMe(upd.me);
        if (!upd.items.length && !upd.removed_ids.length) return;
        const current = messagesRef.current;
        const known = new Set(current.map((m) => m.id));
        const oldest = current[0]?.created_at;
        // changes to messages older than the loaded window are skipped (no gaps)
        const incoming = upd.items.filter((m) => known.has(m.id) || !oldest || m.created_at >= oldest);
        const removed = new Set(upd.removed_ids);
        setMessages((cur) => merge(cur.filter((m) => !removed.has(m.id)), incoming));
        const fresh = incoming.filter((m) => !known.has(m.id) && !m.mine).length;
        if (fresh > 0) {
          if (atBottomRef.current) {
            scrollToBottom();
            readUpTo(merge([...current], incoming));
          } else {
            setNewBelow((n) => n + fresh);
            onUnread(upd.unread);
          }
        }
      } catch {
        setPollFailures((n) => n + 1);
      } finally {
        busy = false;
      }
    };
    const timer = setInterval(tick, POLL_MS);
    const onVisible = () => document.visibilityState === "visible" && tick();
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("online", tick);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("online", tick);
    };
  }, [loaded, loadLatest, onUnread, readUpTo, scrollToBottom]);

  // Escape closes (unless a dialog is open)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !restrict && !editingId && !deleting) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, restrict, editingId, deleting]);

  const loadOlder = useCallback(async () => {
    const first = messagesRef.current[0];
    if (!first || loadingOlder) return;
    setLoadingOlder(true);
    const el = listRef.current;
    const heightBefore = el ? el.scrollHeight : 0;
    const topBefore = el ? el.scrollTop : 0;
    try {
      const page = await getHistory(first.id);
      setMessages((cur) => merge(cur, page.items));
      setHasMore(page.has_more);
      // keep the message the reader was looking at in place
      requestAnimationFrame(() => {
        if (el) el.scrollTop = el.scrollHeight - heightBefore + topBefore;
      });
    } catch {
      setNotice(t("globalChat.err_generic"));
    } finally {
      setLoadingOlder(false);
    }
  }, [loadingOlder, t]);

  function onScroll(e: React.UIEvent<HTMLDivElement>) {
    const el = e.currentTarget;
    const bottom = el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM_PX;
    atBottomRef.current = bottom;
    if (bottom !== atBottom) {
      setAtBottom(bottom);
      if (bottom && newBelow > 0) readUpTo(messagesRef.current);
    }
    if (el.scrollTop < NEAR_TOP_PX && hasMore && !loadingOlder) loadOlder();
  }

  async function send() {
    const body = draft.trim();
    if (!body || sending || body.length > MAX_LENGTH) return;
    setSending(true);
    setSendError(null);
    try {
      const m = await sendMessage(body);
      setMessages((cur) => merge(cur, [m]));
      setDraft("");
      atBottomRef.current = true;
      scrollToBottom();
      inputRef.current?.focus();
    } catch (err) {
      setSendError(errorText(err));
      const code = errorCode(err);
      if (code === "chat_muted" || code === "chat_banned") {
        // the server knows best: refresh the status shown above the input
        getUpdates(syncRef.current ?? new Date().toISOString()).then((u) => setMe(u.me)).catch(() => undefined);
      }
    } finally {
      setSending(false);
    }
  }

  async function saveEdit(m: ChatMessage, body: string) {
    try {
      const updated = await editMessage(m.id, body);
      setMessages((cur) => merge(cur, [updated]));
      setEditingId(null);
    } catch (err) {
      const code = errorCode(err);
      if (code === "chat_muted" || code === "chat_banned") {
        getUpdates(syncRef.current ?? new Date().toISOString()).then((u) => setMe(u.me)).catch(() => undefined);
      }
      throw new Error(errorText(err));
    }
  }

  async function confirmDelete(m: ChatMessage) {
    try {
      await deleteMessage(m.id);
    } catch (err) {
      // already gone (deleted elsewhere / hidden meanwhile): just drop it here too
      if (errorCode(err) !== "Message not found") throw new Error(errorText(err));
    }
    setMessages((cur) => (isModerator ? cur.map((x) => (x.id === m.id ? { ...x, status: "deleted" as const, is_pinned: false } : x)) : cur.filter((x) => x.id !== m.id)));
    setPinned((cur) => cur.filter((p) => p.id !== m.id));
    if (editingId === m.id) setEditingId(null);
    setDeleting(null);
  }

  async function moderate(m: ChatMessage, action: "pin" | "unpin" | "hide" | "unhide" | "approve") {
    let reason: string | undefined;
    if (action === "hide") {
      const answer = window.prompt(t("globalChat.hideReason"));
      if (answer === null) return;
      reason = answer.trim() || undefined;
    }
    try {
      const updated = await moderateMessage(m.id, action, reason);
      setMessages((cur) => merge(cur, [{ ...updated, mine: m.mine }]));
      setPinned((cur) => {
        const rest = cur.filter((p) => p.id !== updated.id);
        return updated.is_pinned ? [updated, ...rest] : rest;
      });
    } catch (err) {
      setNotice(errorText(err));
    }
  }

  const restriction = me?.restriction ?? null;
  const restrictionText = restriction
    ? restriction.kind === "ban"
      ? restriction.permanent ? t("globalChat.bannedForever") : t("globalChat.bannedUntil", { date: fmtDateTime(restriction.ends_at) })
      : t("globalChat.mutedUntil", { date: fmtDateTime(restriction.ends_at) })
    : null;
  const isModerator = !!me?.is_moderator;
  const showPins = pinsOpen ? pinned : pinned.slice(0, 1);

  return (
    <section role="dialog" aria-label={t("globalChat.title")} data-testid="global-chat-panel"
             className="fixed inset-0 z-50 flex flex-col overflow-hidden bg-surface-card text-text-primary sm:inset-auto sm:bottom-6 sm:right-6 sm:h-[min(640px,calc(100dvh-3rem))] sm:w-[400px] sm:rounded-2xl sm:shadow-[var(--shadow-lg)] sm:ring-1 sm:ring-surface-border"
             style={{ paddingTop: "env(safe-area-inset-top)", paddingBottom: "env(safe-area-inset-bottom)" }}>
      <header className="flex items-center gap-3 border-b border-surface-border px-4 py-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-blue/10 text-accent-blue"><MessagesSquare size={18} /></span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm font-bold">{t("globalChat.title")}</h2>
          <p className="truncate text-[11px] text-text-muted">{t("globalChat.subtitle")}</p>
        </div>
        <button type="button" onClick={onClose} aria-label={t("globalChat.close")} data-testid="global-chat-close"
                className="flex h-10 w-10 items-center justify-center rounded-full text-text-secondary hover:bg-surface-hover"><X size={18} /></button>
      </header>

      {pinned.length > 0 && (
        <div className="border-b border-surface-border bg-accent-blue/5 px-4 py-2" data-testid="global-chat-pinned">
          <div className="flex items-center justify-between gap-2">
            <p className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-accent-blue">
              <Pin size={11} /> {pinned.length > 1 ? t("globalChat.pinnedCount", { n: pinned.length }) : t("globalChat.pinned")}
            </p>
            {pinned.length > 1 && (
              <button type="button" onClick={() => setPinsOpen((v) => !v)} aria-expanded={pinsOpen} aria-label={t("globalChat.pinnedCount", { n: pinned.length })}
                      className="rounded p-1 text-accent-blue hover:bg-accent-blue/10"><ChevronDown size={14} className={cn("transition-transform", pinsOpen && "rotate-180")} /></button>
            )}
          </div>
          <ul className={cn("mt-1 space-y-1.5", pinsOpen && "max-h-48 overflow-y-auto")}>
            {showPins.map((p) => (
              <li key={p.id} className="text-xs">
                <p className={cn("whitespace-pre-wrap break-words text-text-primary", !pinsOpen && "line-clamp-2")}>{p.body}</p>
                <p className="mt-0.5 flex items-center gap-2 text-[10px] text-text-muted">
                  <span>{p.sender?.name ?? t("globalChat.deletedUser")} · {fmtDateTime(p.created_at)}</span>
                  {isModerator && <button type="button" onClick={() => moderate(p, "unpin")} className="font-semibold text-accent-blue hover:underline">{t("globalChat.unpin")}</button>}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!online ? (
        <p role="status" className="flex items-center gap-2 bg-amber-500/10 px-4 py-2 text-xs text-amber-700 dark:text-amber-300"><WifiOff size={14} /> {t("globalChat.offline")}</p>
      ) : pollFailures >= 2 ? (
        <p role="status" className="flex items-center gap-2 bg-amber-500/10 px-4 py-2 text-xs text-amber-700 dark:text-amber-300"><Loader2 size={14} className="animate-spin" /> {t("globalChat.reconnecting")}</p>
      ) : null}

      <div ref={listRef} onScroll={onScroll} data-testid="global-chat-list" aria-live="polite" aria-relevant="additions"
           className="relative flex-1 space-y-2 overflow-y-auto overscroll-contain px-3 py-3">
        {!loaded && !loadError && (
          <div className="flex h-full items-center justify-center gap-2 text-sm text-text-muted"><Loader2 size={18} className="animate-spin" /> {t("globalChat.loading")}</div>
        )}
        {loadError && (
          <div role="alert" className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center text-sm text-danger">
            {t("globalChat.loadError")}
            <button type="button" onClick={() => { setLoadError(false); loadLatest().catch(() => setLoadError(true)); }}
                    className="rounded-xl bg-surface-hover px-4 py-2 font-semibold text-text-primary ring-1 ring-surface-border">{t("globalChat.retry")}</button>
          </div>
        )}
        {loaded && hasMore && (
          <button type="button" onClick={loadOlder} disabled={loadingOlder}
                  className="mx-auto flex items-center gap-1.5 rounded-full bg-surface-hover px-3 py-1 text-xs font-semibold text-text-secondary ring-1 ring-surface-border">
            {loadingOlder && <Loader2 size={12} className="animate-spin" />}
            {loadingOlder ? t("globalChat.loadingOlder") : t("globalChat.loadOlder")}
          </button>
        )}
        {loaded && !hasMore && messages.length > 0 && <p className="py-1 text-center text-[11px] text-text-muted">{t("globalChat.historyStart")}</p>}
        {loaded && messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center text-sm text-text-muted">
            <MessagesSquare size={28} className="text-text-muted/60" />
            {t("globalChat.empty")}
          </div>
        )}

        {messages.map((m) => {
          const editing = editingId === m.id;
          const light = m.mine && m.status === "visible" && !editing;  // white text on the blue own bubble
          return (
          <article key={m.id} data-testid="global-chat-message" data-status={m.status} className={cn("group flex", m.mine ? "justify-end" : "justify-start")}>
            <div className={cn("max-w-[85%] rounded-2xl px-3 py-2",
              m.status === "hidden" || m.status === "deleted" ? "border border-dashed border-danger/40 bg-danger/5 opacity-80"
                : editing ? "w-full bg-surface-hover ring-1 ring-accent-blue/40"
                : m.status === "pending" ? "bg-amber-500/10 ring-1 ring-amber-500/40"
                : m.mine ? "bg-accent-blue text-white" : m.sender?.badge ? "bg-amber-500/10 ring-1 ring-amber-500/25" : "bg-surface-hover")}>
              {!m.mine && (
                <p className="mb-0.5 flex flex-wrap items-center gap-1 text-[11px] font-bold text-text-secondary">
                  <span className="break-all">{m.sender?.name ?? t("globalChat.deletedUser")}</span>
                  {m.sender?.badge && <span className="rounded bg-amber-500/20 px-1 text-[10px] font-semibold">{t(`globalChat.badge_${m.sender.badge}`)}</span>}
                </p>
              )}
              {editing ? (
                <EditMessageForm message={m} onSave={(body) => saveEdit(m, body)} onCancel={() => setEditingId(null)} />
              ) : m.body !== null && (
                <p className={cn("whitespace-pre-wrap break-words text-sm", !light && "text-text-primary")}>{m.body}</p>
              )}
              {m.status === "deleted" && (
                <p className="mt-1 text-[11px] text-danger">{t("globalChat.deletedByAuthor")}</p>
              )}
              {m.status === "pending" && (
                <p className="mt-1 flex items-center gap-1 text-[11px] text-amber-700 dark:text-amber-300">
                  <ShieldAlert size={12} /> {isModerator ? `${t("globalChat.pendingMod")}: ${(m.flagged_words ?? []).join(", ")}` : t("globalChat.pending")}
                </p>
              )}
              {m.status === "hidden" && (
                <p className="mt-1 text-[11px] text-danger">{t("globalChat.hiddenMod")}{m.hidden_reason ? `: ${m.hidden_reason}` : ""}</p>
              )}
              {!editing && (
              <div className={cn("mt-1 flex flex-wrap items-center justify-end gap-x-2 gap-y-1 text-[10px]", light ? "text-white/75" : "text-text-muted")}>
                {m.is_pinned && <Pin size={10} aria-label={t("globalChat.pinned")} />}
                {m.edited_at && <span data-testid="global-chat-edited" title={fmtDateTime(m.edited_at)}>{t("globalChat.edited")}</span>}
                <time dateTime={m.created_at} title={fmtDateTime(m.created_at)}>{fmtMessageTime(m.created_at)}</time>
                {m.mine && (
                  <OwnMessageMenu canEdit={canEditOwn(m)} canDelete={canDeleteOwn(m)} boundary={listRef} light={light}
                                  onEdit={() => setEditingId(m.id)} onDelete={() => setDeleting(m)} />
                )}
              </div>
              )}
              {isModerator && m.status !== "deleted" && (
                <div role="group" aria-label={t("globalChat.actions")} className="mt-1 flex flex-wrap justify-end gap-1 opacity-70 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
                  {m.status === "pending" && <ModButton label={t("globalChat.approve")} onClick={() => moderate(m, "approve")}><Check size={12} /></ModButton>}
                  {m.status === "visible" && (m.is_pinned
                    ? <ModButton label={t("globalChat.unpin")} onClick={() => moderate(m, "unpin")}><PinOff size={12} /></ModButton>
                    : <ModButton label={t("globalChat.pin")} onClick={() => moderate(m, "pin")}><Pin size={12} /></ModButton>)}
                  {m.status === "hidden"
                    ? <ModButton label={t("globalChat.unhide")} onClick={() => moderate(m, "unhide")}><Eye size={12} /></ModButton>
                    : <ModButton label={t("globalChat.hide")} onClick={() => moderate(m, "hide")}><EyeOff size={12} /></ModButton>}
                  {m.can_restrict && m.sender && (
                    <>
                      <ModButton label={t("globalChat.mute")} onClick={() => setRestrict({ user: m.sender!, messageId: m.id, kind: "mute" })}><VolumeX size={12} /></ModButton>
                      <ModButton label={t("globalChat.ban")} onClick={() => setRestrict({ user: m.sender!, messageId: m.id, kind: "ban" })}><Ban size={12} /></ModButton>
                    </>
                  )}
                </div>
              )}
            </div>
          </article>
          );
        })}
      </div>

      {!atBottom && loaded && (
        <button type="button" onClick={() => { atBottomRef.current = true; scrollToBottom(); readUpTo(messagesRef.current); }}
                className="absolute bottom-28 left-1/2 inline-flex -translate-x-1/2 items-center gap-1 rounded-full bg-accent-blue px-3 py-1.5 text-xs font-semibold text-white shadow-lg">
          <ArrowDown size={12} /> {newBelow > 0 ? t("globalChat.newMessages", { n: newBelow }) : t("globalChat.latest")}
        </button>
      )}

      <footer className="border-t border-surface-border p-3">
        {notice && (
          <p role="alert" className="mb-2 flex items-start justify-between gap-2 rounded-lg bg-danger/10 px-2.5 py-1.5 text-xs text-danger">
            {notice}<button type="button" onClick={() => setNotice(null)} aria-label={t("globalChat.close")}><X size={12} /></button>
          </p>
        )}
        {done && (
          <p role="status" className="mb-2 flex items-start justify-between gap-2 rounded-lg bg-success/10 px-2.5 py-1.5 text-xs text-success">
            {done}<button type="button" onClick={() => setDone(null)} aria-label={t("globalChat.close")}><X size={12} /></button>
          </p>
        )}
        {restriction ? (
          <div role="status" data-testid="global-chat-restricted" className="rounded-xl bg-danger/10 p-3 text-xs text-danger ring-1 ring-danger/20">
            <p className="font-semibold">{restrictionText}</p>
            {restriction.note && <p className="mt-1 text-text-primary">{t("globalChat.noteLabel")}: {restriction.note}</p>}
            <p className="mt-1 text-text-secondary">{t("globalChat.readOnlyNote")}</p>
          </div>
        ) : (
          <form className="flex items-end gap-2" onSubmit={(e) => { e.preventDefault(); send(); }}>
            <div className="relative flex-1">
              <textarea ref={inputRef} value={draft} rows={1} maxLength={MAX_LENGTH} disabled={!loaded || !me?.can_post}
                        onChange={(e) => { setDraft(e.target.value); setSendError(null); }}
                        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(); } }}
                        placeholder={t("globalChat.placeholder")} aria-label={t("globalChat.placeholder")} aria-describedby="gc-hint" data-testid="global-chat-input"
                        className="block max-h-32 min-h-11 w-full resize-none rounded-xl bg-surface-hover px-3 py-2.5 text-sm text-text-primary ring-1 ring-surface-border outline-none [field-sizing:content] focus:ring-accent-blue disabled:opacity-60" />
              {draft.length > MAX_LENGTH - 200 && (
                <span className={cn("absolute bottom-1 right-2 text-[10px]", draft.length >= MAX_LENGTH ? "text-danger" : "text-text-muted")}>{draft.length}/{MAX_LENGTH}</span>
              )}
            </div>
            <button type="submit" disabled={sending || !draft.trim() || !me?.can_post} aria-label={t("globalChat.send")} data-testid="global-chat-send"
                    className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent-blue text-white disabled:opacity-50">
              {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </form>
        )}
        {sendError && <p role="alert" className="mt-1.5 text-xs text-danger" data-testid="global-chat-send-error">{sendError}</p>}
        {!restriction && <p id="gc-hint" className="mt-1 hidden text-[10px] text-text-muted sm:block">{t("globalChat.hint")}</p>}
      </footer>

      {deleting && <ConfirmDeleteDialog message={deleting} onConfirm={() => confirmDelete(deleting)} onCancel={() => setDeleting(null)} />}

      {restrict && (
        <RestrictDialog target={restrict.user} messageId={restrict.messageId} initialKind={restrict.kind} canBanPermanently={isSuperAdmin}
                        onClose={() => setRestrict(null)}
                        onDone={(r) => {
                          setRestrict(null);
                          setNotice(null);
                          setDone(`${r.user.name}: ${r.kind === "ban" ? t("globalChat.ban") : t("globalChat.mute")} ✓ (${r.permanent ? "∞" : fmtDateTime(r.ends_at)})`);
                        }} />
      )}
    </section>
  );
}

function ModButton({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} title={label}
            className="flex h-7 w-7 items-center justify-center rounded-md bg-surface-card/80 text-text-secondary ring-1 ring-surface-border hover:text-accent-blue">
      {children}
    </button>
  );
}
