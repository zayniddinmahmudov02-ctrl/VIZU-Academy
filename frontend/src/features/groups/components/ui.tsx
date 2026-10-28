"use client";

import type { ReactNode } from "react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { errorCode, type SubmissionStatus, type TaskStatus } from "../groups-service";

export const card = "rounded-card bg-surface-card shadow-[var(--shadow-md)] ring-1 ring-surface-border";
export const input =
  "h-11 w-full rounded-xl bg-surface-hover px-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue";
export const textarea =
  "w-full rounded-xl bg-surface-hover p-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue";
export const primaryBtn =
  "inline-flex min-h-11 items-center justify-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-60";
export const secondaryBtn =
  "inline-flex min-h-11 items-center justify-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border disabled:opacity-60";

export function fmtDate(iso: string | null | undefined, withTime = false): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return withTime
    ? d.toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })
    : d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
}

const TASK_TONE: Record<TaskStatus, string> = {
  not_started: "bg-surface-hover text-text-secondary ring-surface-border",
  in_progress: "bg-accent-blue/10 text-accent-blue ring-accent-blue/30",
  overdue: "bg-danger/10 text-danger ring-danger/30",
  under_review: "bg-amber-500/10 text-amber-700 ring-amber-500/30 dark:text-amber-300",
  needs_revision: "bg-orange-500/10 text-orange-700 ring-orange-500/30 dark:text-orange-300",
  completed: "bg-success/10 text-success ring-success/30",
  completed_late: "bg-success/10 text-success ring-success/30",
};
const SUB_TONE: Record<SubmissionStatus, string> = {
  in_progress: TASK_TONE.in_progress,
  under_review: TASK_TONE.under_review,
  needs_revision: TASK_TONE.needs_revision,
  accepted: TASK_TONE.completed,
};

export function Pill({ className, children }: { className?: string; children: ReactNode }) {
  return <span className={cn("inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1", className)}>{children}</span>;
}

export function TaskBadge({ status }: { status: TaskStatus }) {
  const { t } = useTranslation();
  return <Pill className={TASK_TONE[status]}>{t(`groups.st_${status}`)}</Pill>;
}

export function SubmissionBadge({ status }: { status: SubmissionStatus }) {
  const { t } = useTranslation();
  return <Pill className={SUB_TONE[status]}>{t(`groups.sub_${status}`)}</Pill>;
}

export function LevelPill({ level }: { level: string }) {
  return <Pill className="bg-accent-blue/10 text-accent-blue ring-accent-blue/30">{level}</Pill>;
}

export function StatusPill({ status }: { status: string }) {
  const { t } = useTranslation();
  const tone = status === "active" ? "bg-success/10 text-success ring-success/30"
    : status === "blocked" ? "bg-danger/10 text-danger ring-danger/30"
    : "bg-surface-hover text-text-secondary ring-surface-border";
  return <Pill className={tone}>{t(`groups.status_${status}`)}</Pill>;
}

/** Translated message for a backend error code, falling back to a generic one. */
export function useErrorText() {
  const { t } = useTranslation();
  return (err: unknown) => {
    const code = errorCode(err);
    const key = code ? `groups.err_${code}` : "";
    const text = key ? t(key) : key;
    return text && text !== key ? text : t("groups.err_generic");
  };
}

export function Loading() {
  const { t } = useTranslation();
  return <p className="p-6 text-sm text-text-muted">{t("groups.loading")}</p>;
}

export function ErrorBox({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { t } = useTranslation();
  const text = useErrorText()(error);
  return (
    <div role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger ring-1 ring-danger/20">
      {text === t("groups.err_generic") ? t("groups.loadError") : text}{" "}
      {onRetry && <button type="button" className="font-semibold underline" onClick={onRetry}>{t("groups.retry")}</button>}
    </div>
  );
}

export function Tabs<T extends string>({ tabs, active, onChange }: { tabs: { id: T; label: string; badge?: number }[]; active: T; onChange: (t: T) => void }) {
  return (
    <div role="tablist" className="flex gap-1 overflow-x-auto rounded-xl bg-surface-hover p-1 ring-1 ring-surface-border">
      {tabs.map((tab) => (
        <button key={tab.id} type="button" role="tab" aria-selected={active === tab.id} onClick={() => onChange(tab.id)}
                className={cn("inline-flex min-h-11 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold transition-colors",
                  active === tab.id ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card")}>
          {tab.label}
          {!!tab.badge && <span className={cn("rounded-full px-1.5 text-[10px]", active === tab.id ? "bg-white/25" : "bg-accent-blue text-white")}>{tab.badge}</span>}
        </button>
      ))}
    </div>
  );
}

export function Stat({ label, value, tone }: { label: string; value: ReactNode; tone?: "danger" | "warn" | "ok" }) {
  return (
    <div className={cn(card, "p-4")}>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">{label}</p>
      <p className={cn("mt-1 text-2xl font-bold text-text-primary", tone === "danger" && "text-danger", tone === "warn" && "text-amber-600", tone === "ok" && "text-success")}>{value}</p>
    </div>
  );
}
