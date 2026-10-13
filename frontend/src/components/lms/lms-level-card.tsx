"use client";

import Link from "next/link";
import { ArrowRight, BookOpen, PlayCircle } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import { lessonHref, levelHref } from "@/features/lms/competencies";
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

  return (
    <article className="flex h-full flex-col overflow-hidden rounded-card bg-surface-card shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="lms-level-card" data-level={level.level}>
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
        <h2 className="font-semibold text-text-primary">{level.title}</h2>

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
