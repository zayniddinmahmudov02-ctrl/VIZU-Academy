"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDown, Loader2, Pin, PinOff, Send, Trash2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { getMessages, markRead, moderateMessage, postMessage, type Message } from "../groups-service";
import { card, fmtDate, useErrorText } from "./ui";

const POLL_MS = 5000;
const MAX_LENGTH = 2000;

function merge(current: Message[], incoming: Message[]): Message[] {
  const byId = new Map(current.map((m) => [m.id, m]));
  for (const m of incoming) byId.set(m.id, m);
  return [...byId.values()].sort((a, b) => a.created_at.localeCompare(b.created_at));
}

/** Group chat: newest page first, older pages on demand, new messages by
 *  polling (?after=), plain-text rendering only. */
export default function GroupChat({ groupId, onRead }: { groupId: string; onRead?: () => void }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const [messages, setMessages] = useState<Message[]>([]);
  const [pinned, setPinned] = useState<Message[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [canPost, setCanPost] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [atBottom, setAtBottom] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);
  const lastRef = useRef<string | null>(null);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight }));
  }, []);

  const read = useCallback(() => {
    markRead(groupId).then(() => onRead?.()).catch(() => undefined);
  }, [groupId, onRead]);

  useEffect(() => {
    let alive = true;
    getMessages(groupId)
      .then((page) => {
        if (!alive) return;
        setMessages(page.items);
        setPinned(page.pinned);
        setHasMore(page.has_more);
        setCanPost(page.can_post);
        setLoaded(true);
        lastRef.current = page.items.at(-1)?.created_at ?? null;
        scrollToBottom();
        read();
      })
      .catch((err) => alive && setLoadError(err));
    return () => {
      alive = false;
    };
  }, [groupId, read, scrollToBottom]);

  useEffect(() => {
    if (!loaded) return;
    const timer = setInterval(() => {
      if (document.visibilityState !== "visible") return;
      getMessages(groupId, lastRef.current ? { after: lastRef.current } : {})
        .then((page) => {
          setPinned(page.pinned);
          setCanPost(page.can_post);
          if (page.items.length) {
            setMessages((cur) => merge(cur, page.items));
            lastRef.current = page.items.at(-1)!.created_at;
            if (atBottom) {
              scrollToBottom();
              read();
            }
          }
        })
        .catch(() => undefined);
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [groupId, loaded, atBottom, read, scrollToBottom]);

  async function loadOlder() {
    if (!messages.length) return;
    setLoadingOlder(true);
    const el = listRef.current;
    const before = el ? el.scrollHeight : 0;
    try {
      const page = await getMessages(groupId, { before: messages[0].created_at });
      setMessages((cur) => merge(page.items, cur));
      setHasMore(page.has_more);
      requestAnimationFrame(() => el && el.scrollTo({ top: el.scrollHeight - before }));
    } finally {
      setLoadingOlder(false);
    }
  }

  async function send() {
    const body = draft.trim();
    if (!body) return;
    setSending(true);
    setSendError(null);
    try {
      const m = await postMessage(groupId, body);
      setMessages((cur) => merge(cur, [m]));
      lastRef.current = m.created_at;
      setDraft("");
      scrollToBottom();
    } catch (err) {
      setSendError(errorText(err));
    } finally {
      setSending(false);
    }
  }

  async function moderate(m: Message, data: { delete?: boolean; pinned?: boolean }) {
    if (data.delete && !window.confirm(t("groups.confirmDelete"))) return;
    try {
      const updated = await moderateMessage(groupId, m.id, data);
      setMessages((cur) => merge(cur, [updated]));
      setPinned((cur) => (updated.is_pinned ? merge(cur.filter((p) => p.id !== updated.id), [updated]) : cur.filter((p) => p.id !== updated.id)));
    } catch (err) {
      setSendError(errorText(err));
    }
  }

  if (loadError) return <p role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger">{errorText(loadError)}</p>;

  return (
    <div className={cn(card, "flex h-[min(70vh,640px)] flex-col overflow-hidden")} data-testid="group-chat">
      {pinned.length > 0 && (
        <div className="border-b border-surface-border bg-accent-blue/5 px-4 py-2">
          <p className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-accent-blue"><Pin size={11} /> {t("groups.pinnedMessages")}</p>
          {pinned.map((m) => (
            <p key={m.id} className="mt-0.5 truncate text-xs text-text-secondary"><b>{m.sender?.name}:</b> {m.body}</p>
          ))}
        </div>
      )}

      <div ref={listRef} className="relative flex-1 space-y-2 overflow-y-auto px-3 py-4 sm:px-4"
           onScroll={(e) => {
             const el = e.currentTarget;
             const bottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
             if (bottom !== atBottom) {
               setAtBottom(bottom);
               if (bottom) read();
             }
           }}>
        {!loaded && <Loader2 className="mx-auto animate-spin text-text-muted" />}
        {hasMore && (
          <button type="button" onClick={loadOlder} disabled={loadingOlder}
                  className="mx-auto block rounded-full bg-surface-hover px-3 py-1 text-xs font-semibold text-text-secondary ring-1 ring-surface-border">
            {loadingOlder ? t("groups.loading") : t("groups.loadOlder")}
          </button>
        )}
        {loaded && messages.length === 0 && <p className="py-10 text-center text-sm text-text-muted">{t("groups.noMessages")}</p>}
        {messages.map((m) =>
          m.kind === "system" ? (
            <p key={m.id} className="py-1 text-center text-[11px] text-text-muted">{m.body} · {fmtDate(m.created_at, true)}</p>
          ) : (
            <div key={m.id} className={cn("group flex", m.mine ? "justify-end" : "justify-start")}>
              <div className={cn("max-w-[85%] rounded-2xl px-3 py-2 sm:max-w-[70%]",
                m.mine ? "bg-accent-blue text-white" : m.sender?.is_teacher ? "bg-amber-500/10 ring-1 ring-amber-500/30" : "bg-surface-hover")}>
                {!m.mine && (
                  <p className="mb-0.5 text-[11px] font-bold text-text-secondary">
                    {m.sender?.name}{m.sender?.is_teacher && <span className="ml-1 rounded bg-amber-500/20 px-1 text-[10px]">{t("groups.teacherBadge")}</span>}
                  </p>
                )}
                {m.deleted ? (
                  <p className={cn("text-sm italic", m.mine ? "text-white/80" : "text-text-muted")}>{t("groups.deletedMessage")}</p>
                ) : (
                  <p className={cn("whitespace-pre-wrap break-words text-sm", !m.mine && "text-text-primary")}>{m.body}</p>
                )}
                <div className={cn("mt-1 flex items-center justify-end gap-2 text-[10px]", m.mine ? "text-white/70" : "text-text-muted")}>
                  {m.is_pinned && <Pin size={10} aria-label={t("groups.pinned")} />}
                  <time dateTime={m.created_at}>{fmtDate(m.created_at, true)}</time>
                  {m.can_moderate && (
                    <span className="flex gap-1 opacity-60 group-hover:opacity-100">
                      <button type="button" aria-label={m.is_pinned ? t("groups.unpin") : t("groups.pin")} title={m.is_pinned ? t("groups.unpin") : t("groups.pin")}
                              onClick={() => moderate(m, { pinned: !m.is_pinned })}>{m.is_pinned ? <PinOff size={12} /> : <Pin size={12} />}</button>
                      <button type="button" aria-label={t("groups.remove")} title={t("groups.remove")} onClick={() => moderate(m, { delete: true })}><Trash2 size={12} /></button>
                    </span>
                  )}
                </div>
              </div>
            </div>
          ),
        )}
      </div>

      {!atBottom && (
        <button type="button" onClick={() => { scrollToBottom(); read(); }}
                className="mx-auto -mt-12 mb-2 inline-flex items-center gap-1 rounded-full bg-accent-blue px-3 py-1.5 text-xs font-semibold text-white shadow">
          <ArrowDown size={12} /> {t("groups.latest")}
        </button>
      )}

      <div className="border-t border-surface-border p-3">
        {canPost ? (
          <form className="flex items-end gap-2" onSubmit={(e) => { e.preventDefault(); send(); }}>
            <textarea value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={MAX_LENGTH} rows={1}
                      placeholder={t("groups.writePlaceholder")} aria-label={t("groups.writePlaceholder")} data-testid="chat-input"
                      onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                      className="max-h-32 min-h-11 flex-1 resize-none rounded-xl bg-surface-hover px-3 py-2.5 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue" />
            <button type="submit" disabled={sending || !draft.trim()} aria-label={t("groups.send")}
                    className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent-blue text-white disabled:opacity-50">
              {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </form>
        ) : (
          <p className="text-center text-xs text-text-muted">{t("groups.readOnly")}</p>
        )}
        {sendError && <p role="alert" className="mt-1 text-xs text-danger">{sendError}</p>}
      </div>
    </div>
  );
}
