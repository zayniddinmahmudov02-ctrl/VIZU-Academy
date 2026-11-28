"use client";

import Link from "next/link";
import { ArrowRight, BookOpen, Lock, PlayCircle, RotateCw } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import { lessonHref, levelHref } from "@/features/lms/competencies";
import { accessDate, levelStatus, renewHref, STATUS_TONE } from "@/features/lms/level-status";
import type { LmsLevelSummary } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";

// presentation only — the level list and every number come from the backend
export const LEVEL_GRADIENT: Record<string, string> = {
  A1: "from-emerald-500 to-emerald-400",
  A2: "from-brand-500 to-brand-400",
  B1: "from-brand-700 to-brand-500",
  B2: "from-purple-600 to-purple-500",
  C1: "from-brand-900 to-brand-700",
};

export default function LmsLevelCard({ level }: { level: LmsLevelSummary }) {
  const { t } = useTranslation();
  const gradient = LEVEL_GRADIENT[level.level] ?? "from-brand-600 to-accent-blue";
  const started = level.lessons_completed > 0 || level.last_lesson_id !== null;
  const sale = level.sale;
  const status = levelStatus(level);
  const name = t(`levels.${level.level.toLowerCase()}`);
  const title = name.startsWith("levels.") ? level.title : `${level.level} · ${name}`;

  if (sale?.coming_soon) {
    return (
      <article className="flex h-full flex-col overflow-hidden rounded-card bg-surface-card opacity-90 shadow-[var(--shadow-md)] ring-1 ring-surface-border"
               data-testid="lms-level-card" data-level={level.level} data-status={status} data-coming-soon="true">
        <div className={`relative h-24 overflow-hidden bg-gradient-to-br ${gradient} grayscale-[40%]`}>
          <div className="absolute inset-0 flex items-center justify-between px-6">
            <span className="text-4xl font-bold text-white drop-shadow-sm">{level.level}</span>
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/20 text-white backdrop-blur-md"><Lock size={20} /></span>
          </div>
        </div>
        <div className="flex flex-1 flex-col gap-3 p-5">
          <div className="flex items-start justify-between gap-2">
            <h2 className="font-semibold text-text-primary">{title}</h2>
            <span className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${STATUS_TONE[status]}`} data-testid="lms-level-status">{t(`hub.status.${status}`)}</span>
          </div>
          <p className="text-sm text-text-secondary">{t(`hub.levelDesc.${level.level}`)}</p>
          <p className="text-xs text-text-muted">{t("lms.comingSoonHint")}</p>
          <span className="mt-auto inline-flex items-center justify-center gap-2 rounded-xl bg-surface-hover px-4 py-2.5 text-sm font-semibold text-text-muted">
            <Lock size={15} /> {t("lms.comingSoon")}
          </span>
        </div>
      </article>
    );
  }

  return (
    <article className="flex h-full flex-col overflow-hidden rounded-card bg-surface-card shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="lms-level-card" data-level={level.level} data-status={status}>
      <Link href={levelHref(level.level)} className={`relative block h-24 overflow-hidden bg-gradient-to-br ${gradient}`}>
        <div className="absolute -right-6 -top-10 h-32 w-32 rounded-full bg-white/15 blur-xl" />
        <div className="absolute inset-0 flex items-center justify-between px-6">
          <span className="text-4xl font-bold text-white drop-shadow-sm">{level.level}</span>
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/20 text-white backdrop-blur-md">
            <BookOpen size={20} />
          </span>
        </div>
      </Link>

      <div className="flex flex-1 flex-col gap-4 p-5">
        <div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold text-text-primary">{title}</h2>
            <span className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${STATUS_TONE[status]}`} data-testid="lms-level-status">{t(`hub.status.${status}`)}</span>
          </div>
          <p className="mt-1 text-sm text-text-secondary">{t(`hub.levelDesc.${level.level}`)}</p>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          {sale?.owned ? (
            <span className="flex flex-wrap items-center gap-2">
              <span className="shrink-0 rounded-full bg-success/15 px-2.5 py-1 text-xs font-semibold text-success">{t("lms.owned")}</span>
              {sale.access_until && <span className="text-xs text-text-muted" data-testid="lms-level-access-until">{t("lms.accessUntil", { date: accessDate(sale.access_until) })}</span>}
            </span>
          ) : status === "EXPIRED" ? (
            <span className="flex w-full flex-wrap items-center justify-between gap-2" data-testid="lms-level-expired">
              <span className="text-xs font-medium text-amber-700 dark:text-amber-300">{t("lms.accessExpired", { date: accessDate(sale?.expired_at) })}</span>
              <Link href={renewHref(sale)} data-testid="lms-level-renew"
                    className="inline-flex items-center gap-1 rounded-full bg-amber-500 px-3 py-1 text-xs font-bold text-white hover:opacity-90">
                <RotateCw size={12} /> {t("lms.renew")}
              </Link>
            </span>
          ) : sale?.offer?.purchasable && sale.offer.sale_price ? (
            <span className="shrink-0 rounded-full bg-accent-blue/10 px-2.5 py-1 text-xs font-bold text-accent-blue" data-testid="lms-level-price">
              {t("lms.som", { n: sale.offer.sale_price.toLocaleString("ru-RU").replace(/ /g, " ") })}
            </span>
          ) : sale?.sales_closed ? (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-surface-hover px-2.5 py-1 text-xs font-bold text-text-muted" data-testid="lms-level-sales-closed">
              <Lock size={11} /> {t("lms.comingSoon")}
            </span>
          ) : null}
        </div>
        {sale && !sale.owned && sale.free_lessons > 0 && <p className="-mt-2 text-xs text-text-muted">{t("lms.buyFree")}</p>}

        <dl className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-xl bg-surface-hover/60 px-2 py-2">
            <dt className="text-[11px] text-text-muted">{t("lms.lessonsTotal")}</dt>
            <dd className="text-lg font-bold text-text-primary" data-testid="lms-level-target">{level.lessons_target}</dd>
          </div>
          <div className="rounded-xl bg-surface-hover/60 px-2 py-2">
            <dt className="text-[11px] text-text-muted">{t("lms.lessonsAvailable")}</dt>
            <dd className="text-lg font-bold text-text-primary" data-testid="lms-level-published">{level.lessons_published}</dd>
          </div>
          <div className="rounded-xl bg-surface-hover/60 px-2 py-2">
            <dt className="text-[11px] text-text-muted">{t("lms.lessonsCompleted")}</dt>
            <dd className="text-lg font-bold text-success">{level.lessons_completed}</dd>
          </div>
        </dl>

        <div>
          <div className="mb-1.5 flex justify-between text-xs">
            <span className="text-text-secondary">{t("lms.progress")}</span>
            <span className="font-bold text-accent-blue">{level.percent}%</span>
          </div>
          <ProgressBar value={level.percent} trackClassName="h-1.5" />
        </div>

        <div className="mt-auto flex flex-wrap gap-2">
          {level.continue_lesson_id ? (
            <Link href={lessonHref(level.continue_lesson_id)} data-testid="lms-level-continue"
                  className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-accent-blue px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90">
              <PlayCircle size={16} /> {t(started ? "lms.continue" : "lms.start")}
            </Link>
          ) : (
            <span className="flex-1 rounded-xl bg-surface-hover px-4 py-2.5 text-center text-sm text-text-muted">
              {t(level.lessons_published === 0 ? "lms.levelEmpty" : "lms.levelNothingOpen")}
            </span>
          )}
          <Link href={levelHref(level.level)} aria-label={t("lms.allLessons")}
                className="inline-flex items-center gap-1 rounded-xl px-3 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:text-accent-blue">
            {t("lms.allLessons")} <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </article>
  );
}
