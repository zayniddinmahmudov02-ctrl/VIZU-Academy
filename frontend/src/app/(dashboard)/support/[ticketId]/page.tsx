"use client";

import { use, useRef, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Send } from "lucide-react";

import SupportStatusBadge from "@/features/support/components/support-status-badge";
import { getMyTicket, newRequestId, sendMyMessage, supportErrorKey } from "@/features/support/support-service";
import { useTranslation } from "@/lib/i18n/use-translation";

/** One request: the conversation (plain text) and a reply box. */
export default function SupportTicketPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = use(params);
  const { t, language } = useTranslation();
  const qc = useQueryClient();
  const { data, isLoading, isError } = useQuery({ queryKey: ["support", "ticket", ticketId], queryFn: () => getMyTicket(ticketId), retry: false });
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(newRequestId());
  const locale = language === "uz" ? "uz-UZ" : "de-DE";

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (sending || !text.trim()) return;
    setSending(true);
    setError(null);
    try {
      const ticket = await sendMyMessage(ticketId, text.trim(), requestId.current);
      qc.setQueryData(["support", "ticket", ticketId], ticket);
      setText("");
      requestId.current = newRequestId();
      qc.invalidateQueries({ queryKey: ["support", "mine"] });
    } catch (err) {
      setError(supportErrorKey(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Link href="/support" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue">
        <ArrowLeft size={16} /> {t("support.back")}
      </Link>
      {isLoading ? (
        <div className="h-48 animate-pulse rounded-card bg-surface-hover" aria-busy="true" />
      ) : isError || !data ? (
        <p className="rounded-card bg-surface-card p-8 text-center text-sm text-text-secondary ring-1 ring-surface-border">{t("support.notFound")}</p>
      ) : (
        <>
          <header className="rounded-card bg-surface-card p-5 shadow-[var(--shadow-card)] ring-1 ring-surface-border">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-xs font-semibold text-text-muted">{data.display_number} · {t(`support.cat_${data.category}`)}</p>
                <h1 className="text-lg font-bold text-text-primary">{data.subject}</h1>
              </div>
              <SupportStatusBadge status={data.status} />
            </div>
          </header>

          <ol className="space-y-3" data-testid="support-messages">
            {data.messages.map((m) => {
              const mine = m.author_role === "STUDENT";
              return (
                <li key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${mine ? "bg-accent-blue text-white" : "bg-surface-card text-text-primary ring-1 ring-surface-border"}`}>
                    <p className={`mb-1 text-[11px] font-semibold ${mine ? "text-white/80" : "text-text-muted"}`}>
                      {mine ? t("support.you") : t("support.supportTeam")} · {new Date(m.created_at).toLocaleString(locale, { dateStyle: "medium", timeStyle: "short" })}
                    </p>
                    {/* plain text — never rendered as HTML */}
                    <p className="whitespace-pre-line break-words">{m.body}</p>
                  </div>
                </li>
              );
            })}
          </ol>

          <form onSubmit={send} className="space-y-2 rounded-card bg-surface-card p-4 shadow-[var(--shadow-card)] ring-1 ring-surface-border">
            <label htmlFor="sp-reply" className="block text-xs font-semibold text-text-secondary">{t("support.reply")}</label>
            <textarea id="sp-reply" value={text} maxLength={5000} onChange={(e) => setText(e.target.value)}
                      className="min-h-[100px] w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60" />
            {["ANSWERED", "WAITING", "CLOSED"].includes(data.status) && <p className="text-xs text-text-muted">{t("support.reopenHint")}</p>}
            {error && <p role="alert" className="text-sm text-danger">{t(error)}</p>}
            <button type="submit" disabled={sending || !text.trim()} data-testid="support-reply-send"
                    className="inline-flex items-center gap-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50">
              {sending ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />} {t("support.replySend")}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
