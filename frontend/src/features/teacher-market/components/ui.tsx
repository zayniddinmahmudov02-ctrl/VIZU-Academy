"use client";

/* eslint-disable @next/next/no-img-element -- teacher photos / course images are our own re-encoded WebP files in /uploads */
import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { BadgeCheck, Star, UserRound, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { resolveMediaUrl } from "@/lib/media";
import { cn } from "@/lib/utils";

/** Server error code → readable text (market.err_<CODE>), else the generic message. */
export function useErrorText() {
  const { t } = useTranslation();
  return (err: unknown) => {
    const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
    const raw = data?.message ?? data?.detail;
    const code = typeof raw === "string" ? raw.split(":")[0].trim() : "";
    const key = `market.err_${code}`;
    const text = code ? t(key) : key;
    return text !== key ? text : t("market.error");
  };
}

export function formatPrice(value: number) {
  return new Intl.NumberFormat("ru-RU").format(value).replace(/,/g, " ");
}

export function formatDate(value: string | null | undefined, language: string) {
  if (!value) return "—";
  const d = new Date(value.length === 10 ? `${value}T00:00:00` : value);
  return d.toLocaleDateString(language === "uz" ? "uz-UZ" : "de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function formatDateTime(value: string | null | undefined, language: string) {
  if (!value) return "—";
  return new Date(value).toLocaleString(language === "uz" ? "uz-UZ" : "de-DE", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Tashkent",
  });
}

/** Portrait 9:16 teacher photo (object-cover in a fixed ratio box, never stretched); a neutral placeholder without photo. */
export function TeacherPhoto({ url, name, className }: { url: string | null; name: string; className?: string }) {
  const src = resolveMediaUrl(url);
  return (
    <div className={cn("relative aspect-[9/16] w-full overflow-hidden rounded-2xl bg-gradient-to-b from-brand-700/20 to-brand-900/40", className)}>
      {src ? (
        <img src={src} alt={name} loading="lazy" decoding="async" className="absolute inset-0 h-full w-full object-cover" />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-text-muted" data-testid="teacher-photo-placeholder">
          <UserRound size={56} strokeWidth={1.4} aria-hidden />
        </div>
      )}
    </div>
  );
}

export function VerifiedBadge() {
  const { t } = useTranslation();
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400"
          data-testid="verified-badge">
      <BadgeCheck size={14} aria-hidden /> {t("market.verified")}
    </span>
  );
}

export function Stars({ value, size = 16, className }: { value: number; size?: number; className?: string }) {
  const { t } = useTranslation();
  const rounded = Math.round(value * 2) / 2;
  return (
    <span className={cn("inline-flex items-center gap-0.5", className)} role="img" aria-label={t("market.stars", { n: value.toFixed(1) })}>
      {[1, 2, 3, 4, 5].map((i) => {
        const fill = rounded >= i ? 1 : rounded >= i - 0.5 ? 0.5 : 0;
        return (
          <span key={i} className="relative inline-block" style={{ width: size, height: size }}>
            <Star size={size} className="absolute inset-0 text-amber-400/35" aria-hidden />
            {fill > 0 && (
              <span className="absolute inset-0 overflow-hidden" style={{ width: fill === 1 ? size : size / 2 }}>
                <Star size={size} className="fill-amber-400 text-amber-400" aria-hidden />
              </span>
            )}
          </span>
        );
      })}
    </span>
  );
}

export function StarInput({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex gap-1" role="radiogroup" aria-label={t("market.ratingTitle")}>
      {[1, 2, 3, 4, 5].map((i) => (
        <button key={i} type="button" role="radio" aria-checked={value === i} aria-label={t("market.stars", { n: i })}
                onClick={() => onChange(i)} className="rounded p-1 transition hover:scale-110" data-testid={`star-${i}`}>
          <Star size={28} className={i <= value ? "fill-amber-400 text-amber-400" : "text-amber-400/40"} aria-hidden />
        </button>
      ))}
    </div>
  );
}

const TONES: Record<string, string> = {
  ANMELDUNG: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  BALD: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
  AUSGEBUCHT: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  VORBEREITUNG: "bg-slate-500/10 text-text-secondary",
  LAUFEND: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
  ABGESCHLOSSEN: "bg-slate-500/10 text-text-muted",
  ABGESAGT: "bg-danger/10 text-danger",
  APPROVED: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  PENDING: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  REJECTED: "bg-danger/10 text-danger",
  CANCELLED: "bg-danger/10 text-danger",
  ENDED: "bg-slate-500/10 text-text-muted",
  DRAFT: "bg-slate-500/10 text-text-secondary",
  UNPUBLISHED: "bg-slate-500/10 text-text-secondary",
};

export function Pill({ tone, children, testId }: { tone: string; children: ReactNode; testId?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold", TONES[tone] ?? "bg-slate-500/10 text-text-secondary")}
          data-testid={testId}>
      {children}
    </span>
  );
}

/** Accessible modal (portal to <body>, Escape and the backdrop close it, focus moves inside). */
export function Modal({ open, onClose, title, children, wide, testId }: {
  open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean; testId?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    const first = ref.current?.querySelector<HTMLElement>("input, textarea, select, button");
    first?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open || typeof document === "undefined") return null;
  return createPortal(
    <div className="fixed inset-0 z-[70] flex items-end justify-center sm:items-center" data-testid={testId}>
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden />
      <div ref={ref} role="dialog" aria-modal="true" aria-label={title}
           className={cn("relative z-10 flex max-h-[92dvh] w-full flex-col overflow-hidden rounded-t-3xl bg-surface-card shadow-[var(--shadow-lg)] sm:rounded-3xl",
             wide ? "sm:max-w-3xl" : "sm:max-w-lg")}>
        <div className="flex items-center justify-between gap-3 border-b border-surface-border px-5 py-4">
          <h2 className="min-w-0 truncate text-lg font-bold text-text-primary">{title}</h2>
          <button type="button" onClick={onClose} className="rounded-full p-2 text-text-muted hover:bg-surface-hover" aria-label="Close" data-testid="modal-close">
            <X size={18} />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export const inputClass =
  "w-full rounded-xl bg-surface-bg px-3 py-2.5 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-2 focus:ring-accent-blue";
export const buttonPrimary =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-accent-blue px-4 text-sm font-semibold text-white transition hover:brightness-110 disabled:opacity-50";
export const buttonSecondary =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-surface-hover px-4 text-sm font-semibold text-text-primary ring-1 ring-surface-border transition hover:bg-surface-border/40 disabled:opacity-50";
