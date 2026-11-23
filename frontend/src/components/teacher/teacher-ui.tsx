"use client";

import type { ReactNode } from "react";
import { AlertTriangle, Inbox, Loader2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

/** Building blocks of the Teacher Panel pages (theme tokens of the student / teacher surface). */

export function TeacherPageTitle({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-2xl font-extrabold tracking-tight text-text-primary sm:text-3xl" data-testid="teacher-page-title">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-text-secondary">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Panel({ title, children, className, actions, testId }: { title?: string; children: ReactNode; className?: string; actions?: ReactNode; testId?: string }) {
  return (
    <section className={cn("rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-5", className)} data-testid={testId}>
      {(title || actions) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          {title && <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">{title}</h2>}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function StatTile({ icon: Icon, label, value, hint, testId }: { icon: typeof Inbox; label: string; value: ReactNode; hint?: string; testId?: string }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid={testId}>
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-blue/10 text-accent-blue"><Icon size={22} /></div>
      <div className="min-w-0">
        <p className="text-2xl font-bold text-text-primary" data-testid={testId ? `${testId}-value` : undefined}>{value}</p>
        <p className="text-sm text-text-secondary">{label}</p>
        {hint && <p className="text-xs text-text-muted">{hint}</p>}
      </div>
    </div>
  );
}

export function EmptyState({ text, children, testId }: { text: string; children?: ReactNode; testId?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-surface-border px-4 py-10 text-center" data-testid={testId ?? "empty-state"}>
      <Inbox size={28} className="text-text-muted" aria-hidden />
      <p className="max-w-md text-sm text-text-secondary">{text}</p>
      {children}
    </div>
  );
}

export function ErrorState({ onRetry }: { onRetry?: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl bg-danger/5 px-4 py-8 text-center ring-1 ring-danger/20" role="alert">
      <AlertTriangle size={24} className="text-danger" aria-hidden />
      <p className="text-sm text-danger">{t("tpanel.loadError")}</p>
      {onRetry && <button type="button" onClick={onRetry} className="text-sm font-medium text-accent-blue underline">{t("tpanel.retry")}</button>}
    </div>
  );
}

export function Loading() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-sm text-text-muted" aria-busy="true">
      <Loader2 size={18} className="animate-spin" /> {t("tpanel.loading")}
    </div>
  );
}

const STATUS_TONE: Record<string, string> = {
  active: "bg-success/15 text-success",
  inactive: "bg-surface-hover text-text-secondary",
  blocked: "bg-danger/15 text-danger",
};

export function StudentStatusBadge({ status }: { status: string }) {
  const { t } = useTranslation();
  return <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold", STATUS_TONE[status] ?? STATUS_TONE.inactive)}>{t(`tpanel.status_${status}`)}</span>;
}

export function Pager({ page, pageSize, total, onPage }: { page: number; pageSize: number; total: number; onPage: (p: number) => void }) {
  const { t } = useTranslation();
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-sm text-text-secondary">
      <span>{t("tpanel.pageInfo", { page, pages, total })}</span>
      <span className="flex gap-2">
        <button type="button" disabled={page <= 1} onClick={() => onPage(page - 1)} className="rounded-lg px-3 py-1.5 ring-1 ring-surface-border disabled:opacity-40" data-testid="pager-prev">{t("tpanel.prev")}</button>
        <button type="button" disabled={page >= pages} onClick={() => onPage(page + 1)} className="rounded-lg px-3 py-1.5 ring-1 ring-surface-border disabled:opacity-40" data-testid="pager-next">{t("tpanel.next")}</button>
      </span>
    </div>
  );
}

export const fieldClass = "rounded-xl border border-surface-border bg-surface-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20";
