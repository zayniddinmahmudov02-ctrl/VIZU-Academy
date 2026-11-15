"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Clock, Copy, FileUp, Loader2, Lock, ShoppingCart, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { cancelBookPayment, errorCode, getBookPaymentInfo, getMyBookPayments, submitBookPayment } from "../services/medien-service";
import type { BookPayment, MediaCard, PaymentStatus } from "../types";
import { Cover, formatPrice } from "./media-ui";

/** the receipt: mirrors the server (`MAX_RECEIPT`, `sniff_receipt`): JPG / PNG / WebP image or PDF */
const MAX_RECEIPT_BYTES = 8 * 1024 * 1024;
const RECEIPT_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
const MAX_NOTE = 500;
/** codes the server (or this form) can answer with, each has a `medien.err.<CODE>` text */
const KNOWN_ERRORS = new Set([
  "PAYMENT_PENDING", "ALREADY_OWNED", "NOT_PAID", "RATE_LIMITED", "INVALID_RECEIPT", "UNSUPPORTED_FILE", "FILE_TOO_LARGE", "RECEIPT_OR_NO_RECEIPT", "TRANSFER_TIME_REQUIRED",
  "INVALID_TRANSFER_DATE", "INVALID_TRANSFER_TIME", "TRANSFER_IN_FUTURE", "TRANSFER_TOO_OLD", "NOTE_TOO_LONG", "NOT_FOUND", "INVALID_TRANSITION",
]);

type BookLite = Pick<MediaCard, "id" | "title" | "cover_url" | "price" | "currency" | "locked">;

/** "2026-11-15" and "14:05" in Uzbekistan time (UTC+5, no daylight saving): the transfer is checked against it on the server */
function tashkentNow(): { date: string; time: string } {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date());
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "00";
  return { date: `${get("year")}-${get("month")}-${get("day")}`, time: `${get("hour")}:${get("minute")}` };
}

const groups = (digits: string) => digits.replace(/\D/g, "").replace(/(\d{4})(?=\d)/g, "$1 ");

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const { t } = useTranslation();
  const tone: Record<PaymentStatus, string> = { PENDING: "bg-warning/15 text-warning", APPROVED: "bg-success/15 text-success", REJECTED: "bg-danger/10 text-danger", CANCELLED: "bg-surface-hover text-text-muted" };
  return <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-bold", tone[status])} data-testid="payment-status" data-status={status}>{t(`medien.pay.status.${status}`)}</span>;
}

function useErrorText() {
  const { t } = useTranslation();
  return (err: unknown) => {
    const code = errorCode(err);
    return code && KNOWN_ERRORS.has(code) ? t(`medien.err.${code}`) : t("medien.err.GENERIC");
  };
}

/** The payment form of a PAID book: the card to pay to (copyable), the instruction, then either the receipt (image / PDF) or — without a receipt — the
 * date and time of the transfer. The amount is the book's price and is only shown: the server decides it. A request gives no access: the Super Admin checks the
 * payment and approves it. */
export function BookPaymentModal({ book, onClose }: { book: BookLite; onClose: () => void }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const errorText = useErrorText();
  const fileRef = useRef<HTMLInputElement>(null);
  const [variant, setVariant] = useState<"receipt" | "time">("receipt");
  const [file, setFile] = useState<File | null>(null);
  const [date, setDate] = useState(() => tashkentNow().date);
  const [time, setTime] = useState("");
  const [note, setNote] = useState("");
  const [copied, setCopied] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  const info = useQuery({ queryKey: ["medien-book-payment-info"], queryFn: getBookPaymentInfo, staleTime: 60_000 });
  const mine = useQuery({ queryKey: ["medien-book-payments"], queryFn: getMyBookPayments, staleTime: 5_000 });
  const pending = mine.data?.find((p) => p.book_id === book.id && p.status === "PENDING");
  const today = tashkentNow().date;

  const send = useMutation({
    // only the fields of the chosen variant: a date typed under "without receipt" must not travel with a receipt
    mutationFn: () => submitBookPayment(book.id, { receipt: variant === "receipt" ? file : null, noReceipt: variant === "time", transferDate: variant === "time" ? date : "", transferTime: variant === "time" ? time : "", note }),
    onSuccess: () => {
      setSent(true);
      void queryClient.invalidateQueries({ queryKey: ["medien-book-payments"] });
      void queryClient.invalidateQueries({ queryKey: ["medien-book", book.id] });
    },
    onError: (err) => setProblem(errorText(err)),
  });
  const cancel = useMutation({
    mutationFn: (id: string) => cancelBookPayment(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["medien-book-payments"] });
      void queryClient.invalidateQueries({ queryKey: ["medien-book", book.id] });
    },
    onError: (err) => setProblem(errorText(err)),
  });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    const before = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = before; };
  }, [onClose]);

  async function copyCard() {
    const number = info.data?.card_number;
    if (!number) return;
    try {
      await navigator.clipboard.writeText(number);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setProblem(t("medien.pay.copyFailed"));
    }
  }

  function pickFile(next: File | null) {
    setProblem(null);
    if (next && !RECEIPT_TYPES.includes(next.type)) { setProblem(t("medien.err.UNSUPPORTED_FILE")); setFile(null); return; }
    if (next && next.size > MAX_RECEIPT_BYTES) { setProblem(t("medien.err.FILE_TOO_LARGE")); setFile(null); return; }
    setFile(next);
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setProblem(null);
    if (variant === "receipt" && !file) { setProblem(t("medien.err.RECEIPT_OR_NO_RECEIPT")); return; }
    if (variant === "time") {
      if (!date || !time) { setProblem(t("medien.err.TRANSFER_TIME_REQUIRED")); return; }
      const now = tashkentNow();
      if (date > now.date || (date === now.date && time > now.time)) { setProblem(t("medien.err.TRANSFER_IN_FUTURE")); return; }
    }
    send.mutate();
  }

  const configured = info.data?.configured !== false;
  const field = "w-full rounded-xl bg-surface-hover px-3 py-2.5 text-sm text-text-primary outline-none ring-1 ring-surface-border focus:ring-accent-blue";

  return createPortal(
    <div className="fixed inset-0 z-[75] flex items-end justify-center bg-black/70 p-0 backdrop-blur-sm sm:items-center sm:p-4" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }} data-testid="book-payment-modal">
      <div role="dialog" aria-modal="true" aria-label={t("medien.pay.title")} className="flex max-h-[94dvh] w-full max-w-lg flex-col overflow-hidden rounded-t-3xl bg-surface-card shadow-2xl ring-1 ring-surface-border sm:rounded-3xl">
        <div className="flex items-start gap-3 border-b border-surface-border p-4">
          <Cover src={book.cover_url} kind="BOOK" alt={book.title} className="h-20 w-14 shrink-0 rounded-md shadow-md" />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{t("medien.pay.title")}</p>
            <h2 className="truncate text-base font-extrabold text-text-primary" data-testid="pay-book-title">{book.title}</h2>
            <p className="mt-0.5 text-lg font-extrabold text-accent-blue" data-testid="pay-book-price">{formatPrice(book.price, book.currency)}</p>
          </div>
          <button type="button" onClick={onClose} aria-label={t("medien.close")} data-testid="pay-close" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-text-secondary hover:bg-surface-hover"><X size={18} /></button>
        </div>

        <div className="space-y-4 overflow-y-auto p-4">
          {sent || pending ? (
            <div className="space-y-3 text-center" data-testid="pay-pending">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-warning/15 text-warning"><Clock size={22} /></span>
              <p className="text-base font-bold text-text-primary">{t(sent ? "medien.pay.sentTitle" : "medien.pay.pendingTitle")}</p>
              <p className="text-sm leading-relaxed text-text-secondary">{t("medien.pay.pendingText")}</p>
              <div className="flex flex-col justify-center gap-2 sm:flex-row">
                {pending && !sent && (
                  <button type="button" onClick={() => cancel.mutate(pending.id)} disabled={cancel.isPending} data-testid="pay-cancel"
                          className="rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border disabled:opacity-50">{t("medien.pay.cancel")}</button>
                )}
                <button type="button" onClick={onClose} data-testid="pay-done" className="rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90">{t("medien.close")}</button>
              </div>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4" noValidate>
              <p className="text-sm leading-relaxed text-text-secondary" data-testid="pay-instruction">{t("medien.pay.instruction")}</p>

              <div className="rounded-2xl bg-surface-hover p-3.5" data-testid="pay-card">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">{t("medien.pay.card")}</p>
                {info.isLoading ? <Loader2 size={16} className="mt-1 animate-spin text-text-muted" /> : configured ? (
                  <div className="mt-1 flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-mono text-lg font-bold tracking-wide text-text-primary" data-testid="pay-card-number">{groups(info.data?.card_number ?? "")}</p>
                      {info.data?.card_holder && <p className="truncate text-xs text-text-secondary" data-testid="pay-card-holder">{info.data.card_holder}</p>}
                    </div>
                    <button type="button" onClick={() => void copyCard()} data-testid="pay-copy"
                            className="flex shrink-0 items-center gap-1.5 rounded-lg border border-surface-border px-3 py-1.5 text-xs font-semibold text-text-secondary transition-colors hover:bg-surface-card">
                      {copied ? <Check size={13} className="text-success" /> : <Copy size={13} />}{copied ? t("medien.pay.copied") : t("medien.pay.copy")}
                    </button>
                  </div>
                ) : <p className="mt-1 text-sm text-danger" role="alert">{t("medien.pay.noCard")}</p>}
              </div>

              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary" htmlFor="pay-amount">{t("medien.pay.amount")}</label>
                <input id="pay-amount" value={formatPrice(book.price, book.currency)} readOnly aria-readonly="true" data-testid="pay-amount" className={cn(field, "font-semibold")} />
              </div>

              <div className="grid grid-cols-2 gap-1 rounded-xl bg-surface-hover p-1" role="tablist">
                {(["receipt", "time"] as const).map((v) => (
                  <button key={v} type="button" role="tab" aria-selected={variant === v} onClick={() => { setVariant(v); setProblem(null); }} data-testid={`pay-variant-${v}`}
                          className={cn("rounded-lg px-2 py-2 text-xs font-semibold transition", variant === v ? "bg-surface-card text-text-primary shadow-sm" : "text-text-secondary")}>
                    {t(v === "receipt" ? "medien.pay.withReceipt" : "medien.pay.withoutReceipt")}
                  </button>
                ))}
              </div>

              {variant === "receipt" ? (
                <div>
                  <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp,application/pdf" className="sr-only" id="pay-receipt" data-testid="pay-receipt" onChange={(e) => pickFile(e.target.files?.[0] ?? null)} />
                  <label htmlFor="pay-receipt" className="flex cursor-pointer items-center gap-3 rounded-xl border border-dashed border-surface-border p-3 text-sm text-text-secondary hover:bg-surface-hover">
                    <FileUp size={18} className="shrink-0" />
                    <span className="min-w-0 flex-1 truncate" data-testid="pay-receipt-name">{file ? file.name : t("medien.pay.chooseReceipt")}</span>
                  </label>
                  <p className="mt-1 text-xs text-text-muted">{t("medien.pay.receiptHint")}</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="mb-1 block text-xs font-semibold text-text-secondary" htmlFor="pay-date">{t("medien.pay.date")}</label>
                    <input id="pay-date" type="date" value={date} max={today} onChange={(e) => setDate(e.target.value)} className={field} data-testid="pay-date" />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold text-text-secondary" htmlFor="pay-time">{t("medien.pay.time")}</label>
                    <input id="pay-time" type="time" value={time} onChange={(e) => setTime(e.target.value)} className={field} data-testid="pay-time" />
                  </div>
                  <p className="col-span-2 text-xs text-text-muted">{t("medien.pay.timeHint")}</p>
                </div>
              )}

              <div>
                <label className="mb-1 block text-xs font-semibold text-text-secondary" htmlFor="pay-note">{t("medien.pay.note")}</label>
                <textarea id="pay-note" value={note} maxLength={MAX_NOTE} rows={2} onChange={(e) => setNote(e.target.value)} className={cn(field, "resize-none")} data-testid="pay-note" />
              </div>

              {problem && <p role="alert" className="rounded-xl bg-danger/10 p-3 text-sm text-danger" data-testid="pay-error">{problem}</p>}

              <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                <button type="button" onClick={onClose} className="rounded-xl bg-surface-hover px-4 py-2.5 text-sm font-semibold text-text-primary ring-1 ring-surface-border">{t("medien.pay.back")}</button>
                <button type="submit" disabled={send.isPending || !configured} data-testid="pay-submit"
                        className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50">
                  {send.isPending ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />}{t("medien.pay.submit")}
                </button>
              </div>
            </form>
          )}
          {(sent || pending) && problem && <p role="alert" className="rounded-xl bg-danger/10 p-3 text-sm text-danger">{problem}</p>}
        </div>
      </div>
    </div>,
    document.body,
  );
}

/** "Jetzt kaufen" of a locked BOOK: opens the payment form; a request that waits for the admin or was rejected (with the reason) is shown instead of a second
 * request. `open` / `onOpenChange` let the page (the reader's paywall) open the form too. */
export function BookBuyButton({ book, className, size = "md", open, onOpenChange }: { book: BookLite; className?: string; size?: "sm" | "md"; open?: boolean; onOpenChange?: (open: boolean) => void }) {
  const { t } = useTranslation();
  const [inner, setInner] = useState(false);
  const shown = open ?? inner;
  const setShown = (next: boolean) => { if (onOpenChange) onOpenChange(next); else setInner(next); };
  const mine = useQuery({ queryKey: ["medien-book-payments"], queryFn: getMyBookPayments, enabled: book.locked, staleTime: 15_000 });
  if (!book.locked) return null;
  const latest = mine.data?.find((p) => p.book_id === book.id);
  const pending = latest?.status === "PENDING";
  const rejected = latest?.status === "REJECTED";
  const sizing = size === "sm" ? "px-3 py-1.5 text-xs" : "px-5 py-2.5 text-sm";
  return (
    <div className={className}>
      <button type="button" onClick={() => setShown(true)} data-testid="book-buy"
              className={cn("inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition hover:opacity-90", sizing, pending ? "bg-warning/15 text-warning" : "bg-accent-blue text-white")}>
        {pending ? <Clock size={14} /> : <ShoppingCart size={14} />}{pending ? t("medien.pay.pendingShort") : rejected ? t("medien.pay.retry") : t("medien.buy")}
      </button>
      {rejected && latest?.admin_note && size === "md" && (
        <p className="mt-2 flex items-start gap-2 rounded-xl bg-danger/10 p-3 text-sm text-danger" data-testid="book-payment-rejected"><Lock size={14} className="mt-0.5 shrink-0" /><span>{t("medien.pay.rejectedWhy", { reason: latest.admin_note })}</span></p>
      )}
      {shown && <BookPaymentModal book={book} onClose={() => setShown(false)} />}
    </div>
  );
}

/** The student's own payment requests (status, reason of a rejection, cancel while pending) */
export function MyBookPayments() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const errorText = useErrorText();
  const list = useQuery({ queryKey: ["medien-book-payments"], queryFn: getMyBookPayments, staleTime: 15_000 });
  const cancel = useMutation({
    mutationFn: (id: string) => cancelBookPayment(id),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ["medien-book-payments"] }); void queryClient.invalidateQueries({ queryKey: ["medien-book"] }); },
  });
  const rows: BookPayment[] = list.data ?? [];
  if (!rows.length) return null;
  return (
    <section className="space-y-3" data-testid="my-book-payments">
      <h2 className="text-lg font-bold text-text-primary sm:text-xl">{t("medien.pay.mine")}</h2>
      <ul className="divide-y divide-surface-border rounded-2xl bg-surface-card ring-1 ring-surface-border">
        {rows.map((p) => (
          <li key={p.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3" data-testid="my-payment-row">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-text-primary">{p.book_title ?? "—"}</p>
              <p className="text-xs text-text-muted">{formatPrice(p.amount, p.currency)} · {new Date(p.created_at).toLocaleDateString()}</p>
              {p.status === "REJECTED" && p.admin_note && <p className="mt-1 text-xs text-danger">{t("medien.pay.rejectedWhy", { reason: p.admin_note })}</p>}
            </div>
            <PaymentStatusBadge status={p.status} />
            {p.can_cancel && (
              <button type="button" onClick={() => cancel.mutate(p.id)} disabled={cancel.isPending} data-testid="my-payment-cancel" className="rounded-lg px-3 py-1.5 text-xs font-semibold text-text-secondary ring-1 ring-surface-border hover:bg-surface-hover disabled:opacity-50">{t("medien.pay.cancel")}</button>
            )}
          </li>
        ))}
      </ul>
      {cancel.isError && <p role="alert" className="text-xs text-danger">{errorText(cancel.error)}</p>}
    </section>
  );
}
