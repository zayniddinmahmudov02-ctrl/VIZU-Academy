"use client";

import { Suspense, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Send, X } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminPageHeader, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  assignSupportTicket,
  getSupportTicket,
  listSupportStaff,
  listSupportTickets,
  replySupportTicket,
  setSupportStatus,
  type TicketFilters,
} from "@/features/admin/services/support-admin-service";
import { SUPPORT_CATEGORIES, SUPPORT_STATUSES, newRequestId } from "@/features/support/support-service";

const STATUS_LABEL: Record<string, string> = { NEW: "Neu", IN_PROGRESS: "In Bearbeitung", WAITING: "Warten auf Antwort", ANSWERED: "Beantwortet", CLOSED: "Geschlossen" };
const CAT_LABEL: Record<string, string> = { COURSE: "Kurs / Lektionen", PAYMENT: "Zahlung / Bezahlung", MEDIA: "Audio / Video", TESTS: "Tests / Prüfung",
  CERTIFICATE: "Zertifikat", TECHNICAL: "Technisches Problem", OTHER: "Sonstiges" };
const fmt = (iso: string) => new Date(iso).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });

export default function SupportAdminPage() {
  return (
    <Suspense fallback={null}>
      <SupportAdmin />
    </Suspense>
  );
}

/** Admin -> Support / Hilfeanfragen: filterable list, conversation, reply,
 * status and assignment. Every rule (permissions, "Beantwortet" only after a
 * reply, notification to the student) is enforced by the backend. */
function SupportAdmin() {
  const qc = useQueryClient();
  const searchParams = useSearchParams();
  const [filters, setFilters] = useState<TicketFilters>({ page: 1 });
  const [openId, setOpenId] = useState<string | null>(() => searchParams.get("ticket"));
  const list = useQuery({ queryKey: ["admin", "support", filters], queryFn: () => listSupportTickets(filters) });
  const staff = useQuery({ queryKey: ["admin", "support", "staff"], queryFn: listSupportStaff });
  const set = (p: Partial<TicketFilters>) => setFilters((f) => ({ ...f, ...p, page: p.page ?? 1 }));
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;

  return (
    <div className="space-y-6" data-testid="admin-support">
      <AdminPageHeader title="Support / Hilfeanfragen" description="Fragen der Studenten beantworten. Jede Antwort benachrichtigt den Studenten." />

      <AdminCard>
        <div className="mb-3 flex flex-wrap gap-2">
          <button type="button" onClick={() => set({ status: undefined })}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold ring-1 ${!filters.status ? "bg-[var(--admin-primary)] text-white ring-[var(--admin-primary)]" : "text-[var(--admin-text-secondary)] ring-[var(--admin-border-strong)]"}`}>Alle</button>
          {SUPPORT_STATUSES.map((s) => (
            <button key={s} type="button" onClick={() => set({ status: s })} data-testid={`sp-filter-${s}`}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold ring-1 ${filters.status === s ? "bg-[var(--admin-primary)] text-white ring-[var(--admin-primary)]" : "text-[var(--admin-text-secondary)] ring-[var(--admin-border-strong)]"}`}>
              {STATUS_LABEL[s]} ({list.data?.counts?.[s] ?? 0})
            </button>
          ))}
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <div><AdminLabel>Suche</AdminLabel><AdminInput placeholder="Betreff, Student, #Nr." value={filters.q ?? ""} onChange={(e) => set({ q: e.target.value })} /></div>
          <div><AdminLabel>Kategorie</AdminLabel>
            <AdminSelect value={filters.category ?? ""} onChange={(e) => set({ category: e.target.value || undefined })}>
              <option value="">Alle</option>{SUPPORT_CATEGORIES.map((c) => <option key={c} value={c}>{CAT_LABEL[c]}</option>)}
            </AdminSelect></div>
          <div><AdminLabel>Von</AdminLabel><AdminInput type="date" value={filters.date_from ?? ""} onChange={(e) => set({ date_from: e.target.value || undefined })} /></div>
          <div><AdminLabel>Bis</AdminLabel><AdminInput type="date" value={filters.date_to ?? ""} onChange={(e) => set({ date_to: e.target.value || undefined })} /></div>
          <div><AdminLabel>Zuständig</AdminLabel>
            <AdminSelect value={filters.assigned ?? ""} onChange={(e) => set({ assigned: e.target.value || undefined })}>
              <option value="">Alle</option><option value="me">Mir zugewiesen</option><option value="none">Nicht zugewiesen</option>
            </AdminSelect></div>
        </div>
      </AdminCard>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <AdminCard className="overflow-x-auto p-0">
          {list.isLoading ? <div className="p-6"><Loader2 className="animate-spin text-[var(--admin-text-muted)]" /></div> : list.isError ? (
            <p className="p-6 text-sm text-[var(--admin-danger)]">{apiErrorMessage(list.error, "Konnte nicht geladen werden (Support-Berechtigung nötig).")}</p>
          ) : (list.data?.items ?? []).length === 0 ? <p className="p-6 text-sm text-[var(--admin-text-muted)]">Keine Anfragen.</p> : (
            <table className="w-full min-w-[620px] text-left text-sm">
              <thead className="text-[11px] uppercase tracking-wide text-[var(--admin-text-muted)]">
                <tr className="border-b border-[var(--admin-border)]">{["Nr.", "Betreff", "Student", "Status", "Letzte Nachricht"].map((h) => <th key={h} className="px-3 py-2.5">{h}</th>)}</tr>
              </thead>
              <tbody>
                {list.data!.items.map((tk) => (
                  <tr key={tk.id} onClick={() => setOpenId(tk.id)} data-testid="sp-row"
                      className={`cursor-pointer border-b border-[var(--admin-border)] last:border-0 hover:bg-white/5 ${openId === tk.id ? "bg-white/5" : ""}`}>
                    <td className="px-3 py-2.5 font-mono text-xs text-[var(--admin-text-secondary)]">{tk.display_number}</td>
                    <td className="max-w-[220px] px-3 py-2.5"><p className="truncate font-semibold text-[var(--admin-text-primary)]">{tk.subject}</p><p className="text-xs text-[var(--admin-text-muted)]">{CAT_LABEL[tk.category]}</p></td>
                    <td className="max-w-[180px] px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]"><p className="truncate">{tk.student?.name}</p><p className="truncate text-[var(--admin-text-muted)]">{tk.student?.email}</p></td>
                    <td className="px-3 py-2.5 text-xs font-semibold text-[var(--admin-text-primary)]">{STATUS_LABEL[tk.status]}{tk.assigned_to && <span className="block font-normal text-[var(--admin-text-muted)]">{tk.assigned_to.name}</span>}</td>
                    <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{fmt(tk.last_message_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {pages > 1 && (
            <div className="flex items-center gap-2 p-3 text-sm text-[var(--admin-text-secondary)]">
              <AdminButton size="sm" variant="secondary" disabled={(filters.page ?? 1) <= 1} onClick={() => set({ page: (filters.page ?? 1) - 1 })}>Zurück</AdminButton>
              Seite {filters.page ?? 1} / {pages}
              <AdminButton size="sm" variant="secondary" disabled={(filters.page ?? 1) >= pages} onClick={() => set({ page: (filters.page ?? 1) + 1 })}>Weiter</AdminButton>
            </div>
          )}
        </AdminCard>

        {openId && <TicketPanel id={openId} staff={staff.data ?? []} onClose={() => setOpenId(null)} onChanged={() => qc.invalidateQueries({ queryKey: ["admin", "support"] })} />}
      </div>
    </div>
  );
}

function TicketPanel({ id, staff, onClose, onChanged }: { id: string; staff: { id: string; name: string | null }[]; onClose: () => void; onChanged: () => void }) {
  const qc = useQueryClient();
  const { data, isLoading, isError, error } = useQuery({ queryKey: ["admin", "support", "ticket", id], queryFn: () => getSupportTicket(id), retry: false });
  const [reply, setReply] = useState("");
  const [replyStatus, setReplyStatus] = useState("ANSWERED");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const requestId = useRef(newRequestId());

  async function act(fn: () => Promise<unknown>, ok: string) {
    setBusy(true);
    setMsg(null);
    try {
      const updated = await fn();
      qc.setQueryData(["admin", "support", "ticket", id], updated);
      setMsg({ ok: true, text: ok });
      onChanged();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Aktion fehlgeschlagen.") });
    } finally {
      setBusy(false);
    }
  }

  return (
    <AdminCard data-testid="sp-panel">
      <div className="mb-3 flex items-start justify-between gap-2">
        {data ? (
          <div className="min-w-0">
            <p className="text-xs text-[var(--admin-text-muted)]">{data.display_number} · {CAT_LABEL[data.category]} · erstellt {fmt(data.created_at)}</p>
            <h3 className="font-semibold text-[var(--admin-text-primary)]">{data.subject}</h3>
            <p className="text-xs text-[var(--admin-text-secondary)]">{data.student?.name} · {data.student?.email}</p>
          </div>
        ) : <span />}
        <button type="button" onClick={onClose} aria-label="Schließen" className="rounded-lg p-1.5 text-[var(--admin-text-secondary)] hover:bg-white/5"><X size={16} /></button>
      </div>
      {isLoading ? <Loader2 className="animate-spin text-[var(--admin-text-muted)]" /> : isError || !data ? (
        <p className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(error, "Anfrage nicht gefunden.")}</p>
      ) : (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div><AdminLabel>Status</AdminLabel>
              <AdminSelect value={data.status} disabled={busy} onChange={(e) => act(() => setSupportStatus(id, e.target.value), "Status geändert.")} data-testid="sp-status">
                {SUPPORT_STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
              </AdminSelect></div>
            <div><AdminLabel>Zuständig</AdminLabel>
              <AdminSelect value={data.assigned_to?.id ?? ""} disabled={busy} onChange={(e) => act(() => assignSupportTicket(id, e.target.value || null), "Zuständigkeit gespeichert.")}>
                <option value="">— niemand —</option>{staff.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </AdminSelect></div>
          </div>
          <ol className="max-h-[420px] space-y-2 overflow-y-auto rounded-xl bg-white/5 p-3">
            {data.messages.map((m) => (
              <li key={m.id} className={`rounded-xl p-3 text-sm ${m.author_role === "STAFF" ? "ml-6 bg-[var(--admin-primary)]/15" : "mr-6 bg-white/5"}`}>
                <p className="mb-1 text-[11px] font-semibold text-[var(--admin-text-muted)]">{m.author_role === "STAFF" ? `Support · ${m.author_name ?? ""}` : `Student · ${m.author_name ?? ""}`} · {fmt(m.created_at)}</p>
                <p className="whitespace-pre-line break-words text-[var(--admin-text-primary)]">{m.body}</p>
              </li>
            ))}
          </ol>
          <div>
            <AdminLabel>Antwort an den Studenten</AdminLabel>
            <AdminTextarea rows={4} maxLength={5000} value={reply} onChange={(e) => setReply(e.target.value)} data-testid="sp-reply" />
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <AdminSelect value={replyStatus} onChange={(e) => setReplyStatus(e.target.value)} className="w-52">
                {["ANSWERED", "WAITING", "IN_PROGRESS", "CLOSED"].map((s) => <option key={s} value={s}>danach: {STATUS_LABEL[s]}</option>)}
              </AdminSelect>
              <AdminButton disabled={busy || !reply.trim()} data-testid="sp-reply-send"
                           onClick={() => act(async () => {
                             const r = await replySupportTicket(id, reply.trim(), replyStatus, requestId.current);
                             setReply("");
                             requestId.current = newRequestId();
                             return r;
                           }, "Antwort gesendet — der Student wurde benachrichtigt.")}>
                {busy ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />} Antworten
              </AdminButton>
            </div>
          </div>
          {msg && <p role="status" className={`text-sm ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`}>{msg.text}</p>}
        </div>
      )}
    </AdminCard>
  );
}
