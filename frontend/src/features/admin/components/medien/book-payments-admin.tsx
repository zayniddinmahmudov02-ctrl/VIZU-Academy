"use client";

/* eslint-disable @next/next/no-img-element -- the receipt is an object URL of a Bearer-fetched blob: next/image cannot load it */

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ExternalLink, Loader2, ShieldCheck, X } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminLabel, AdminTextarea } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  decideBookPayment, getBookPayment, getBookPaymentReceipt, getBookPaymentSettings, getBookPayments, medienError, saveBookPaymentSettings,
  type BookPaymentDetail, type BookPaymentRow, type PaymentStatus,
} from "@/features/admin/services/medien-admin-service";

import { fileSize } from "./shared";

const PAGE = 25;
const STATUS_DE: Record<PaymentStatus, string> = { PENDING: "Offen", APPROVED: "Bestätigt", REJECTED: "Abgelehnt", CANCELLED: "Storniert" };
const STATUS_TONE: Record<PaymentStatus, string> = {
  PENDING: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]", APPROVED: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]",
  REJECTED: "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]", CANCELLED: "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]",
};
const FILTERS: ("" | PaymentStatus)[] = ["PENDING", "", "APPROVED", "REJECTED", "CANCELLED"];

const money = (n: number | null | undefined, currency = "UZS") => (n == null ? "—" : `${new Intl.NumberFormat("de-DE").format(n)} ${currency}`);
const dateTime = (iso: string | null | undefined) => (iso ? new Intl.DateTimeFormat("de-DE", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso)) : "—");
/** "2026-11-15" -> "15.11.2026" */
const day = (iso: string | null | undefined) => (iso ? iso.split("-").reverse().join(".") : "—");

function StatusPill({ status }: { status: PaymentStatus }) {
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_TONE[status]}`} data-testid="payment-status" data-status={status}>{STATUS_DE[status]}</span>;
}

/** The card students are told to pay to: number (16–19 digits) and the holder's name. Without a number the academy's VIZU Pay card is used. */
function CardSettings() {
  const queryClient = useQueryClient();
  const settings = useQuery({ queryKey: ["admin-book-payment-settings"], queryFn: getBookPaymentSettings });
  const [number, setNumber] = useState<string | null>(null);
  const [holder, setHolder] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const save = useMutation({
    // only what was edited: saving the holder must not copy the default (VIZU Pay) card number into the setting
    mutationFn: () => saveBookPaymentSettings({ ...(number !== null ? { card_number: number } : {}), ...(holder !== null ? { card_holder: holder } : {}) }),
    onSuccess: (data) => { setNumber(null); setHolder(null); setMsg({ ok: true, text: "Kartendaten gespeichert." }); queryClient.setQueryData(["admin-book-payment-settings"], data); },
    onError: (e) => setMsg({ ok: false, text: medienError(e) }),
  });
  const shownNumber = number ?? (settings.data?.card_number ?? "").replace(/(\d{4})(?=\d)/g, "$1 ");
  return (
    <AdminCard className="mb-5">
      <h2 className="mb-1 text-sm font-semibold text-[var(--admin-text-primary)]">Zahlungskarte für Bücher</h2>
      <p className="mb-3 text-xs text-[var(--admin-text-muted)]">Diese Karte sehen Studenten im Zahlungsfenster. Leer lassen = die Karte aus VIZU Pay.</p>
      <form className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]" onSubmit={(e) => { e.preventDefault(); save.mutate(); }} data-testid="card-settings">
        <div><AdminLabel htmlFor="card-number">Kartennummer</AdminLabel><AdminInput id="card-number" inputMode="numeric" autoComplete="off" value={shownNumber} maxLength={23} onChange={(e) => setNumber(e.target.value)} data-testid="card-number" /></div>
        <div><AdminLabel htmlFor="card-holder">Name des Karteninhabers</AdminLabel><AdminInput id="card-holder" autoComplete="off" value={holder ?? settings.data?.card_holder ?? ""} maxLength={80} onChange={(e) => setHolder(e.target.value)} data-testid="card-holder" /></div>
        <div className="flex items-end"><AdminButton disabled={save.isPending || (number === null && holder === null)} data-testid="card-save">{save.isPending ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Speichern</AdminButton></div>
      </form>
      {msg && <p role="status" className={`mt-2 text-sm ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="card-message">{msg.text}</p>}
    </AdminCard>
  );
}

/** The receipt of a request: fetched with the admin's token (never a public URL) and shown from a short-lived object URL. */
function Receipt({ row }: { row: BookPaymentRow }) {
  const blob = useQuery({ queryKey: ["admin-book-payment-receipt", row.id], queryFn: () => getBookPaymentReceipt(row.id), enabled: row.has_receipt, staleTime: Infinity, gcTime: 0, retry: false });
  const url = useMemo(() => (blob.data ? URL.createObjectURL(blob.data) : null), [blob.data]);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  if (!row.has_receipt) {
    return (
      <div className="rounded-xl bg-[var(--admin-warning)]/10 p-3 text-sm text-[var(--admin-text-primary)]" data-testid="receipt-none">
        <p className="font-semibold">Ohne Beleg</p>
        <p className="mt-1 text-[var(--admin-text-secondary)]">Der Student gibt an, am <strong>{day(row.transfer_date)}</strong> um <strong>{row.transfer_time ?? "—"}</strong> Uhr (Usbekistan, UTC+5) überwiesen zu haben. Bitte im Kontoauszug der Karte prüfen.</p>
      </div>
    );
  }
  if (blob.isLoading) return <p className="text-sm text-[var(--admin-text-muted)]"><Loader2 size={14} className="mr-1 inline animate-spin" /> Beleg wird geladen …</p>;
  if (blob.isError || !url) return <p role="alert" className="text-sm text-[var(--admin-danger)]" data-testid="receipt-error">Der Beleg konnte nicht geladen werden (Datei fehlt?).</p>;
  const isPdf = blob.data?.type === "application/pdf" || row.receipt_type === "pdf";
  return (
    <div data-testid="receipt-view" className="space-y-2">
      {isPdf ? <iframe src={url} title="Beleg" className="h-80 w-full rounded-lg bg-white" sandbox="" /> : <img src={url} alt="Beleg" className="max-h-96 w-full rounded-lg bg-white object-contain" data-testid="receipt-image" />}
      <a href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--admin-primary)] hover:underline" data-testid="receipt-open"><ExternalLink size={12} /> In neuem Tab öffnen{row.receipt_size ? ` · ${fileSize(row.receipt_size)}` : ""}</a>
    </div>
  );
}

function Info({ label, children, testId }: { label: string; children: React.ReactNode; testId?: string }) {
  return <div><dt className="text-xs text-[var(--admin-text-muted)]">{label}</dt><dd className="break-words text-sm font-medium text-[var(--admin-text-primary)]" data-testid={testId}>{children}</dd></div>;
}

/** One request with everything the Super Admin checks before deciding (student, book and its current price, the receipt or the transfer time, earlier
 * requests, purchase history) and the decision: approve (after ticking that the payment was checked) or reject with a reason the student sees. */
function PaymentDialog({ id, onClose }: { id: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const detail = useQuery({ queryKey: ["admin-book-payment", id], queryFn: () => getBookPayment(id), retry: false });
  const [verified, setVerified] = useState(false);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const done = (data: BookPaymentDetail, text: string) => {
    queryClient.setQueryData(["admin-book-payment", id], data);
    setMsg({ ok: true, text });
    void queryClient.invalidateQueries({ queryKey: ["admin-book-payments"] });
    void queryClient.invalidateQueries({ queryKey: ["admin-medien-stats"] });
    void queryClient.invalidateQueries({ queryKey: ["admin-medien-purchases"] });
  };
  const decide = useMutation({
    mutationFn: (status: "APPROVED" | "REJECTED") => decideBookPayment(id, status, reason),
    onSuccess: (data, status) => done(data, status === "APPROVED" ? "Zahlung bestätigt: das Buch ist für den Studenten freigeschaltet." : "Zahlung abgelehnt: der Student sieht den Grund."),
    onError: (e) => {
      setMsg({ ok: false, text: medienError(e) });
      void queryClient.invalidateQueries({ queryKey: ["admin-book-payment", id] }); // somebody else may have decided meanwhile
      void queryClient.invalidateQueries({ queryKey: ["admin-book-payments"] });
    },
  });
  const p = detail.data;
  const pending = p?.status === "PENDING";
  const priceChanged = !!p && p.book_price != null && p.book_price !== p.amount;

  return (
    <FormDialog open onOpenChange={(o) => { if (!o && !decide.isPending) onClose(); }} title="Zahlungsanfrage prüfen" size="xl"
                footer={<AdminButton variant="ghost" onClick={onClose} disabled={decide.isPending} data-testid="payment-close">Schließen</AdminButton>}>
      <div className="space-y-5" data-testid="payment-dialog">
        {detail.isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Laden …</p>}
        {detail.isError && <p role="alert" className="text-sm text-[var(--admin-danger)]">{medienError(detail.error)}</p>}
        {p && (
          <>
            <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <Info label="Student" testId="payment-student">{p.user_name ?? "—"}</Info>
              <Info label="E-Mail">{p.user_email ?? "—"}</Info>
              <Info label="Benutzer-ID"><span className="font-mono text-xs">{p.user_id}</span></Info>
              <Info label="Buch" testId="payment-book">{p.book_title ?? "—"}{!p.book_exists && " (gelöscht)"}</Info>
              <Info label="Betrag der Anfrage" testId="payment-amount">{money(p.amount, p.currency)}</Info>
              <Info label="Aktueller Buchpreis">{money(p.book_price, p.currency)}</Info>
              <Info label="Eingereicht">{dateTime(p.created_at)}</Info>
              <Info label="Überweisung (Datum · Uhrzeit)">{day(p.transfer_date)}{p.transfer_time ? ` · ${p.transfer_time}` : ""}</Info>
              <Info label="Status"><StatusPill status={p.status} /></Info>
            </dl>
            {priceChanged && <p className="rounded-xl bg-[var(--admin-warning)]/10 p-3 text-sm text-[var(--admin-text-primary)]" role="status" data-testid="payment-price-changed">Der Buchpreis hat sich seit der Anfrage geändert ({money(p.amount, p.currency)} → {money(p.book_price, p.currency)}). Bitte den überwiesenen Betrag genau prüfen.</p>}
            {p.note && <div><p className="text-xs text-[var(--admin-text-muted)]">Notiz des Studenten</p><p className="whitespace-pre-line text-sm text-[var(--admin-text-primary)]" data-testid="payment-note">{p.note}</p></div>}

            <div><p className="mb-2 text-xs font-semibold uppercase text-[var(--admin-text-muted)]">Beleg</p><Receipt row={p} /></div>

            {pending ? (
              <div className="space-y-3 rounded-xl bg-[var(--admin-hover)] p-4" data-testid="payment-decision">
                <label className="flex cursor-pointer items-start gap-3 text-sm text-[var(--admin-text-primary)]">
                  <AdminCheckbox checked={verified} onCheckedChange={setVerified} aria-label="Zahlung geprüft" data-testid="payment-verified" />
                  <span><ShieldCheck size={14} className="mr-1 inline text-[var(--admin-primary)]" />Ich habe die Zahlung geprüft: Betrag, Datum und Uhrzeit stimmen mit dem Eingang auf der Karte überein.</span>
                </label>
                <div>
                  <AdminLabel htmlFor="payment-reason">Grund / Notiz (beim Ablehnen Pflicht — der Student sieht ihn)</AdminLabel>
                  <AdminTextarea id="payment-reason" rows={2} maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} data-testid="payment-reason" />
                </div>
                <div className="flex flex-wrap justify-end gap-2">
                  <AdminButton variant="danger" disabled={decide.isPending || reason.trim().length < 3} onClick={() => decide.mutate("REJECTED")} data-testid="payment-reject"><X size={14} /> Ablehnen</AdminButton>
                  <AdminButton disabled={decide.isPending || !verified || !p.book_exists} onClick={() => decide.mutate("APPROVED")} data-testid="payment-approve">{decide.isPending ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Bestätigen & freischalten</AdminButton>
                </div>
              </div>
            ) : (
              <div className="rounded-xl bg-[var(--admin-hover)] p-4 text-sm" data-testid="payment-decided">
                <p className="font-semibold text-[var(--admin-text-primary)]">{STATUS_DE[p.status]}{p.reviewed_at ? ` · ${dateTime(p.reviewed_at)}` : ""}{p.reviewed_by_name ? ` · ${p.reviewed_by_name}` : ""}</p>
                {p.admin_note && <p className="mt-1 text-[var(--admin-text-secondary)]">{p.admin_note}</p>}
              </div>
            )}
            {msg && <p role="status" className={`text-sm ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="payment-message">{msg.text}</p>}

            {!!p.history.length && (
              <div data-testid="payment-history">
                <p className="mb-1 text-xs font-semibold uppercase text-[var(--admin-text-muted)]">Frühere Anfragen für dieses Buch</p>
                <ul className="space-y-1 text-sm">{p.history.map((h) => <li key={h.id} className="flex flex-wrap gap-x-3"><StatusPill status={h.status} /><span>{dateTime(h.created_at)}</span><span>{money(h.amount, h.currency)}</span>{h.admin_note && <span className="text-[var(--admin-text-secondary)]">— {h.admin_note}</span>}</li>)}</ul>
              </div>
            )}
            <div data-testid="payment-purchases">
              <p className="mb-1 text-xs font-semibold uppercase text-[var(--admin-text-muted)]">Kaufhistorie des Studenten</p>
              {p.purchases.length ? (
                <ul className="space-y-1 text-sm">{p.purchases.map((x) => <li key={x.id} className="flex flex-wrap gap-x-3"><span className="font-medium">{x.title ?? "—"}</span><span className="text-[var(--admin-text-muted)]">{x.status}</span><span>{money(x.price)}</span><span className="text-[var(--admin-text-muted)]">{dateTime(x.decided_at)}</span></li>)}</ul>
              ) : <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Käufe.</p>}
            </div>
          </>
        )}
      </div>
    </FormDialog>
  );
}

/** Admin → Medien → Bibliothek → Zahlungsanfragen (Super Admin): student, book, amount, receipt, date and time, status; review, approve, reject. */
export default function BookPaymentsAdmin() {
  const [status, setStatus] = useState<"" | PaymentStatus>("PENDING");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<string | null>(null);
  const list = useQuery({ queryKey: ["admin-book-payments", status, q, page], queryFn: () => getBookPayments({ status, q, page, page_size: PAGE }), placeholderData: (prev) => prev, retry: false });

  if (list.isError) {
    return <AdminCard><h2 className="mb-1 text-sm font-semibold text-[var(--admin-text-primary)]">Zahlungsanfragen</h2><p className="text-sm text-[var(--admin-text-muted)]" data-testid="payments-forbidden">Zahlungsanfragen für Bücher sind dem Super Admin vorbehalten.</p></AdminCard>;
  }
  const counts = list.data?.counts;
  const total = list.data?.total ?? 0;
  return (
    <div data-testid="book-payments-admin">
      <CardSettings />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => (
          <button key={f || "ALL"} type="button" onClick={() => { setStatus(f); setPage(1); }} data-testid={`payments-filter-${f || "ALL"}`} aria-pressed={status === f}
                  className={`rounded-full px-3.5 py-1.5 text-sm font-semibold transition ${status === f ? "bg-[var(--admin-primary)] text-white" : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)] hover:bg-[var(--admin-hover)]"}`}>
            {f ? STATUS_DE[f] : "Alle"}{counts && f ? <span className="ml-1.5 text-xs opacity-80">{counts[f]}</span> : null}
          </button>
        ))}
        <AdminInput className="ml-auto w-64" placeholder="Student oder Buch suchen …" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Suchen" data-testid="payments-search" />
      </div>
      <AdminCard className="overflow-x-auto p-0">
        <table className="w-full min-w-[960px] text-left text-sm" data-testid="payments-table">
          <thead><tr className="text-xs uppercase text-[var(--admin-text-muted)]"><th className="p-3">Student</th><th>Buch</th><th>Betrag</th><th>Beleg</th><th>Überweisung</th><th>Eingereicht</th><th>Status</th><th className="pr-3 text-right">Aktion</th></tr></thead>
          <tbody>
            {(list.data?.items ?? []).map((r) => (
              <tr key={r.id} className="border-t border-[var(--admin-border)] align-middle" data-testid="payment-row" data-status={r.status} data-title={r.book_title ?? ""}>
                <td className="p-3"><span className="block font-semibold text-[var(--admin-text-primary)]">{r.user_name ?? "—"}</span><span className="block text-xs text-[var(--admin-text-muted)]">{r.user_email} · <span className="font-mono">{r.user_id.slice(0, 8)}</span></span></td>
                <td className="max-w-[16rem] truncate">{r.book_title ?? "— (Buch gelöscht)"}</td>
                <td>{money(r.amount, r.currency)}</td>
                <td>{r.has_receipt ? `Ja (${(r.receipt_type ?? "").toUpperCase()})` : <span className="text-[var(--admin-warning)]">Ohne Beleg</span>}</td>
                <td>{r.transfer_date ? `${day(r.transfer_date)} ${r.transfer_time ?? ""}` : "—"}</td>
                <td>{dateTime(r.created_at)}</td>
                <td><StatusPill status={r.status} /></td>
                <td className="pr-3 text-right"><AdminButton size="sm" variant={r.status === "PENDING" ? "primary" : "secondary"} onClick={() => setOpen(r.id)} data-testid="payment-review">{r.status === "PENDING" ? "Prüfen" : "Ansehen"}</AdminButton></td>
              </tr>
            ))}
            {list.data && !list.data.items.length && <tr><td colSpan={8} className="p-8 text-center text-[var(--admin-text-muted)]" data-testid="payments-empty">Keine Zahlungsanfragen.</td></tr>}
            {list.isLoading && <tr><td colSpan={8} className="p-8 text-center text-[var(--admin-text-muted)]">Laden …</td></tr>}
          </tbody>
        </table>
      </AdminCard>
      {total > PAGE && <div className="mt-3 flex items-center justify-center gap-3 text-sm"><AdminButton size="sm" variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Zurück</AdminButton><span>{page} / {Math.ceil(total / PAGE)}</span><AdminButton size="sm" variant="secondary" disabled={page >= Math.ceil(total / PAGE)} onClick={() => setPage(page + 1)}>Weiter</AdminButton></div>}
      {open && <PaymentDialog key={open} id={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
