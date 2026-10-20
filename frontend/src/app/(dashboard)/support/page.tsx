"use client";

import { Suspense, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronRight, LifeBuoy, Loader2, Plus, Send } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import SupportStatusBadge from "@/features/support/components/support-status-badge";
import { SUPPORT_CATEGORIES, createTicket, listMyTickets, newRequestId, supportErrorKey, type SupportTicket } from "@/features/support/support-service";
import { useTranslation } from "@/lib/i18n/use-translation";

const input = "w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60";

export default function SupportPage() {
  return (
    <Suspense fallback={null}>
      <SupportPageInner />
    </Suspense>
  );
}

/** "Hilfe & Support": new request form (`?new` opens it, e.g. from "Nachricht
 * schreiben") + the student's own requests. */
function SupportPageInner() {
  const { t, language } = useTranslation();
  const qc = useQueryClient();
  const searchParams = useSearchParams();
  const [showForm, setShowForm] = useState(() => searchParams.has("new"));
  const [subject, setSubject] = useState("");
  const [category, setCategory] = useState("");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<SupportTicket | null>(null);
  const requestId = useRef<string>(newRequestId()); // the same id for retries of this one request
  const locale = language === "uz" ? "uz-UZ" : "de-DE";

  const list = useInfiniteQuery({
    queryKey: ["support", "mine"],
    queryFn: ({ pageParam }) => listMyTickets(pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.page_size < last.total ? last.page + 1 : undefined),
  });
  const tickets = list.data?.pages.flatMap((p) => p.items) ?? [];

  function check(): string | null {
    if (subject.trim().length < 3) return "support.errSubjectShort";
    if (subject.trim().length > 160) return "support.errSubjectLong";
    if (!category) return "support.errCategory";
    if (message.trim().length < 10) return "support.errMessageShort";
    if (message.trim().length > 5000) return "support.errMessageLong";
    return null;
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (sending) return; // double-submit guard (the server is idempotent as well)
    const problem = check();
    if (problem) return setError(problem);
    setSending(true);
    setError(null);
    try {
      const ticket = await createTicket({ subject: subject.trim(), category, message: message.trim(), request_id: requestId.current });
      setCreated(ticket);
      setSubject("");
      setCategory("");
      setMessage("");
      setShowForm(false);
      requestId.current = newRequestId();
      await qc.invalidateQueries({ queryKey: ["support", "mine"] });
    } catch (err) {
      setError(supportErrorKey(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader icon={LifeBuoy} titleKey="support.pageTitle" subtitleKey="support.pageSubtitle" gradient="from-emerald-500 to-accent-blue" />

      <div className="mx-auto max-w-3xl space-y-6">
        {created && (
          <div role="status" className="rounded-card bg-success/10 p-4 text-sm font-medium text-success ring-1 ring-success/20" data-testid="support-created">
            {t("support.created", { number: created.display_number })}{" "}
            <Link href={`/support/${created.id}`} className="font-semibold underline">{created.subject}</Link>
          </div>
        )}

        {showForm ? (
          <form onSubmit={submit} noValidate className="space-y-4 rounded-card bg-surface-card p-5 shadow-[var(--shadow-card)] ring-1 ring-surface-border" data-testid="support-form">
            <h2 className="font-bold text-text-primary">{t("support.newRequest")}</h2>
            <div>
              <label htmlFor="sp-subject" className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("support.subject")}</label>
              <input id="sp-subject" className={input} value={subject} maxLength={160} placeholder={t("support.subjectPlaceholder")} onChange={(e) => setSubject(e.target.value)} />
            </div>
            <div>
              <label htmlFor="sp-category" className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("support.category")}</label>
              <select id="sp-category" className={input} value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">—</option>
                {SUPPORT_CATEGORIES.map((c) => <option key={c} value={c}>{t(`support.cat_${c}`)}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="sp-message" className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("support.message")}</label>
              <textarea id="sp-message" className={`${input} min-h-[140px]`} value={message} maxLength={5000} placeholder={t("support.messagePlaceholder")}
                        onChange={(e) => setMessage(e.target.value)} />
              <p className="mt-1 text-right text-[11px] text-text-muted">{message.length} / 5000</p>
            </div>
            {error && <p role="alert" className="text-sm text-danger" data-testid="support-error">{t(error)}</p>}
            <div className="flex flex-wrap gap-2">
              <button type="submit" disabled={sending} data-testid="support-send"
                      className="inline-flex items-center gap-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50">
                {sending ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />} {sending ? t("support.sending") : t("support.send")}
              </button>
              <button type="button" onClick={() => { setShowForm(false); setError(null); }} className="rounded-xl px-4 py-2.5 text-sm font-semibold text-text-secondary hover:bg-surface-hover">
                {t("support.cancel")}
              </button>
            </div>
          </form>
        ) : (
          <button type="button" onClick={() => { setShowForm(true); setCreated(null); }} data-testid="support-new"
                  className="inline-flex items-center gap-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90">
            <Plus size={15} /> {t("support.newRequest")}
          </button>
        )}

        <section className="rounded-card bg-surface-card p-3 shadow-[var(--shadow-card)] ring-1 ring-surface-border sm:p-5">
          <h2 className="mb-3 px-1 font-bold text-text-primary">{t("support.myRequests")}</h2>
          {list.isLoading ? (
            <div className="space-y-2" aria-busy="true">{[0, 1].map((i) => <div key={i} className="h-14 animate-pulse rounded-xl bg-surface-hover" />)}</div>
          ) : list.isError ? (
            <p className="py-6 text-center text-sm text-text-secondary">
              {t("support.loadError")}{" "}
              <button type="button" onClick={() => list.refetch()} className="font-semibold text-accent-blue hover:underline">{t("support.retry")}</button>
            </p>
          ) : tickets.length === 0 ? (
            <p className="py-8 text-center text-sm text-text-secondary">{t("support.empty")}</p>
          ) : (
            <ul className="divide-y divide-surface-border">
              {tickets.map((tk) => (
                <li key={tk.id}>
                  <Link href={`/support/${tk.id}`} className="flex items-center gap-3 rounded-xl px-2 py-3 hover:bg-surface-hover" data-testid="support-ticket">
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-semibold text-text-primary">{tk.display_number} · {tk.subject}</span>
                      <span className="block text-xs text-text-muted">
                        {t(`support.cat_${tk.category}`)} · {t("support.updated", { date: new Date(tk.last_message_at).toLocaleString(locale, { dateStyle: "medium", timeStyle: "short" }) })}
                      </span>
                    </span>
                    <SupportStatusBadge status={tk.status} />
                    <ChevronRight size={16} className="text-text-muted" aria-hidden="true" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {list.hasNextPage && (
            <button type="button" onClick={() => list.fetchNextPage()} className="mt-2 w-full rounded-xl py-2 text-sm font-semibold text-accent-blue hover:bg-surface-hover">
              {t("support.loadMore")}
            </button>
          )}
        </section>
      </div>
    </div>
  );
}
