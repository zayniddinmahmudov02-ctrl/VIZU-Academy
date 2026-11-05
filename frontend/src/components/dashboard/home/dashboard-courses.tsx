"use client";

import { useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight, BookOpen, ChevronDown, Lock, PlayCircle } from "lucide-react";

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
    // A light tile inside the one shared "A1–C1 Kurse" frame: no shadow / ring of its own.
    <article
      className={`flex h-full min-h-[184px] min-w-0 flex-col overflow-hidden rounded-xl bg-surface-hover/60 ${soon ? "opacity-80" : ""}`}
      data-testid="dashboard-course" data-level={level.level} data-coming-soon={soon || undefined}
    >
      {soon ? (
        <div className={`flex h-14 items-center justify-between bg-gradient-to-br px-3 text-white grayscale-[40%] ${style?.gradient ?? "from-brand-600 to-accent-blue"}`}>
          <span className="text-2xl font-bold">{level.level}</span>
          <Lock size={18} aria-hidden="true" />
        </div>
      ) : (
        <Link href={levelHref(level.level)} prefetch={false} aria-label={t("dashboard.courseOpenAria", { level: level.level })}
              className={`flex h-14 items-center justify-between bg-gradient-to-br px-3 text-white transition-opacity hover:opacity-95 ${style?.gradient ?? "from-brand-600 to-accent-blue"}`}>
          <span className="text-2xl font-bold">{level.level}</span>
          <BookOpen size={18} aria-hidden="true" />
        </Link>
      )}

      <div className="flex flex-1 flex-col gap-2 p-3">
        <div>
          <h3 className="min-h-10 font-semibold leading-snug text-text-primary">{name}</h3>
          <p className="text-xs text-text-muted">{t("dashboard.courseLessons", { count: level.lessons_target })}</p>
        </div>
        {status && (
          <span className={`w-fit max-w-full rounded-full px-2 py-1 text-[10px] font-semibold leading-snug ${owned ? "bg-success/15 text-success" : "bg-surface-hover text-text-secondary"}`}>
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
            <span className="flex min-h-10 w-full items-center justify-center gap-1.5 rounded-xl bg-surface-hover px-2 py-2 text-xs font-semibold text-text-muted" aria-disabled="true">
              <Lock size={14} aria-hidden="true" /> {t("dashboard.ctaSoon")}
            </span>
          ) : learnHref ? (
            <Link href={learnHref} prefetch={false} data-testid="dashboard-course-learn"
                  className="flex min-h-10 w-full items-center justify-center gap-1 rounded-xl bg-accent-blue px-2 py-2 text-xs font-semibold text-white transition-opacity hover:opacity-90">
              <PlayCircle size={15} aria-hidden="true" /> {t("dashboard.ctaLearn")}
            </Link>
          ) : (
            <Link href={levelHref(level.level)} prefetch={false} data-testid="dashboard-course-open"
                  className="flex min-h-10 w-full items-center justify-center gap-1 rounded-xl px-2 py-2 text-xs font-semibold text-accent-blue ring-1 ring-accent-blue/30 transition-colors hover:bg-accent-blue/10">
              {t("dashboard.ctaOpen")} <ArrowRight size={14} aria-hidden="true" />
            </Link>
          )}
        </div>
      </div>
    </article>
  );
}

/** Dashboard: ONE frame "A1–C1 Kurse" holding the five existing course summaries (access-aware links).
 * The header toggles the list (open on every visit; closing only lasts for this page view). */
export default function DashboardCourses() {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const [open, setOpen] = useState(true);
  const { data, isLoading, isError, refetch } = useLmsLevels();
  const count = data?.levels.length ?? 5;

  return (
    <section aria-labelledby="dashboard-courses-title" data-testid="dashboard-courses" data-open={open}
             className="rounded-card bg-surface-card shadow-[var(--shadow-card)] ring-1 ring-surface-border">
      <div className="flex items-start gap-2 p-3 sm:p-4">
        <div className="min-w-0 flex-1">
          {/* disclosure pattern: the heading holds the toggle button (a heading may not sit inside a button) */}
          <h2 id="dashboard-courses-title" className="text-base font-bold text-text-primary">
            <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-controls="dashboard-courses-panel"
                    title={t("dashboard.coursesToggle")} data-testid="dashboard-courses-toggle"
                    className="flex min-h-[44px] w-full items-center gap-2 rounded-lg text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-blue">
              <span>{t("dashboard.coursesTitle")}</span>
              <span className="rounded-full bg-accent-blue/10 px-2 py-0.5 text-[11px] font-semibold text-accent-blue" data-testid="dashboard-courses-count">
                {t("dashboard.coursesCount", { n: count })}
              </span>
              <ChevronDown size={20} aria-hidden="true"
                           className={`ml-auto shrink-0 text-text-secondary transition-transform duration-300 motion-reduce:transition-none ${open ? "rotate-180" : ""}`} />
            </button>
          </h2>
          <p className="-mt-1 text-xs text-text-muted sm:text-sm">{t("dashboard.coursesSubtitle")}</p>
        </div>
        <Link href="/kurse" prefetch={false}
              className="mt-2.5 hidden shrink-0 items-center gap-1.5 text-sm font-semibold text-accent-blue hover:text-accent-blue-hover sm:inline-flex">
          {t("dashboard.allCourses")} <ArrowRight size={15} aria-hidden="true" />
        </Link>
      </div>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div id="dashboard-courses-panel" data-testid="dashboard-courses-panel" key="panel"
                      initial={reduce ? { opacity: 0 } : { height: 0, opacity: 0 }}
                      animate={reduce ? { opacity: 1 } : { height: "auto", opacity: 1 }}
                      exit={reduce ? { opacity: 0 } : { height: 0, opacity: 0 }}
                      transition={{ duration: 0.28, ease: "easeOut" }}
                      className="overflow-hidden">
            <div className="border-t border-surface-border p-3 sm:p-4">
              {isLoading ? (
                <div className="grid auto-rows-fr grid-cols-2 gap-2.5 md:grid-cols-3 xl:grid-cols-5" aria-busy="true" aria-label={t("dashboard.loading")}>
                  {[0, 1, 2, 3, 4].map((i) => <div key={i} className="min-h-[184px] animate-pulse rounded-xl bg-surface-hover" />)}
                </div>
              ) : isError || !data ? (
                <p className="text-sm text-text-secondary">
                  {t("dashboard.loadError")}{" "}
                  <button type="button" onClick={() => refetch()} className="font-semibold text-accent-blue hover:underline">{t("dashboard.retry")}</button>
                </p>
              ) : (
                <div className="grid auto-rows-fr grid-cols-2 gap-2.5 md:grid-cols-3 xl:grid-cols-5">
                  {data.levels.map((level) => <CourseCard key={level.level} level={level} />)}
                </div>
              )}
              <Link href="/kurse" prefetch={false}
                    className="mt-3 inline-flex min-h-10 items-center gap-1.5 text-sm font-semibold text-accent-blue hover:text-accent-blue-hover sm:hidden">
                {t("dashboard.allCourses")} <ArrowRight size={15} aria-hidden="true" />
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
