"use client";

import Link from "next/link";
import { ArrowRight, BookOpen, Lock, PlayCircle } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import { germanLevels } from "@/constants/levels";
import { lessonHref, levelHref } from "@/features/lms/competencies";
import { useLmsLevels } from "@/features/lms/hooks/use-lms";
import type { LmsLevelSummary } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";

const STYLE = new Map<string, (typeof germanLevels)[number]>(germanLevels.map((l) => [l.code, l]));

/** One A1–C1 card. Everything comes from GET /lms/levels (lessons, progress,
 * sale state) — the card only links; every lesson / purchase is checked by
 * the backend again. */
function CourseCard({ level }: { level: LmsLevelSummary }) {
  const { t } = useTranslation();
  const style = STYLE.get(level.level);
  const sale = level.sale;
  const soon = !!sale?.coming_soon;
  const owned = !!sale?.owned;
  const started = level.lessons_completed > 0 || level.last_lesson_id !== null;
  const name = style ? t(style.labelKey) : level.title;

  const status = soon ? t("dashboard.courseComingSoon")
    : owned ? t("dashboard.courseOwned")
      : sale?.sales_closed ? t("dashboard.courseSalesClosed")
        : sale && sale.free_lessons > 0 ? t("dashboard.courseFreeFirst") : null;
  // "Jetzt lernen" opens the lesson to continue with (lesson 1 for a new student), otherwise the course
  const learnHref = level.continue_lesson_id ? lessonHref(level.continue_lesson_id) : null;

  return (
    <article
      className={`flex h-full flex-col overflow-hidden rounded-card bg-surface-card shadow-[var(--shadow-card)] ring-1 ring-surface-border ${soon ? "opacity-80" : ""}`}
      data-testid="dashboard-course" data-level={level.level} data-coming-soon={soon || undefined}
    >
      {soon ? (
        <div className={`flex h-20 items-center justify-between bg-gradient-to-br px-5 text-white grayscale-[40%] ${style?.gradient ?? "from-brand-600 to-accent-blue"}`}>
          <span className="text-3xl font-bold">{level.level}</span>
          <Lock size={18} aria-hidden="true" />
        </div>
      ) : (
        <Link href={levelHref(level.level)} prefetch={false} aria-label={t("dashboard.courseOpenAria", { level: level.level })}
              className={`flex h-20 items-center justify-between bg-gradient-to-br px-5 text-white transition-opacity hover:opacity-95 ${style?.gradient ?? "from-brand-600 to-accent-blue"}`}>
          <span className="text-3xl font-bold">{level.level}</span>
          <BookOpen size={18} aria-hidden="true" />
        </Link>
      )}

      <div className="flex flex-1 flex-col gap-2.5 p-4">
        <div>
          <h3 className="font-semibold leading-snug text-text-primary">{name}</h3>
          <p className="text-xs text-text-muted">{t("dashboard.courseLessons", { count: level.lessons_target })}</p>
        </div>
        {status && (
          <span className={`w-fit rounded-full px-2.5 py-1 text-[11px] font-semibold ${owned ? "bg-success/15 text-success" : "bg-surface-hover text-text-secondary"}`}>
            {status}
          </span>
        )}
        {!soon && started && (
          <div>
            <ProgressBar value={level.percent} trackClassName="h-1.5" />
            <p className="mt-1 text-[11px] text-text-muted">
              {t("dashboard.courseProgress", { done: level.lessons_completed, total: level.lessons_published, percent: level.percent })}
            </p>
          </div>
        )}

        <div className="mt-auto pt-1">
          {soon ? (
            <span className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-surface-hover px-3 py-2 text-sm font-semibold text-text-muted" aria-disabled="true">
              <Lock size={14} aria-hidden="true" /> {t("dashboard.ctaSoon")}
            </span>
          ) : learnHref ? (
            <Link href={learnHref} prefetch={false} data-testid="dashboard-course-learn"
                  className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-accent-blue px-3 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90">
              <PlayCircle size={15} aria-hidden="true" /> {t("dashboard.ctaLearn")}
            </Link>
          ) : (
            <Link href={levelHref(level.level)} prefetch={false} data-testid="dashboard-course-open"
                  className="flex w-full items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold text-accent-blue ring-1 ring-accent-blue/30 transition-colors hover:bg-accent-blue/10">
              {t("dashboard.ctaOpen")} <ArrowRight size={14} aria-hidden="true" />
            </Link>
          )}
        </div>
      </div>
    </article>
  );
}

/** Dashboard: A1–C1 directly under the Werbung banner. */
export default function DashboardCourses() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useLmsLevels();

  return (
    <section aria-labelledby="dashboard-courses-title" data-testid="dashboard-courses">
      <div className="mb-4 flex items-center justify-between">
        <h2 id="dashboard-courses-title" className="text-base font-bold text-text-primary">{t("dashboard.coursesTitle")}</h2>
        <Link href="/kurse" prefetch={false} className="inline-flex items-center gap-1.5 text-sm font-semibold text-accent-blue hover:text-accent-blue-hover">
          {t("dashboard.allCourses")} <ArrowRight size={15} aria-hidden="true" />
        </Link>
      </div>
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5" aria-busy="true" aria-label={t("dashboard.loading")}>
          {[0, 1, 2, 3, 4].map((i) => <div key={i} className="h-[220px] animate-pulse rounded-card bg-surface-hover" />)}
        </div>
      ) : isError || !data ? (
        <p className="rounded-card bg-surface-card p-5 text-sm text-text-secondary ring-1 ring-surface-border">
          {t("dashboard.loadError")}{" "}
          <button type="button" onClick={() => refetch()} className="font-semibold text-accent-blue hover:underline">{t("dashboard.retry")}</button>
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {data.levels.map((level) => <CourseCard key={level.level} level={level} />)}
        </div>
      )}
    </section>
  );
}
