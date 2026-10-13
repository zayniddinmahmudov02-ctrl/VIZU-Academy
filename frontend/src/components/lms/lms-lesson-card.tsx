"use client";

import Link from "next/link";
import { Clock, Crown, Lock, PlayCircle, Video } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import { lessonHref } from "@/features/lms/competencies";
import type { LmsLessonCard as Card } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import LmsStatusBadge from "./lms-status-badge";

const LOCK_HINT: Record<string, string> = {
  PREMIUM_REQUIRED: "lms.lockPremiumShort",
  PREVIOUS_LESSON_NOT_COMPLETED: "lms.lockSequentialShort",
  ADMIN_LOCKED: "lms.lockAdminShort",
};

export default function LmsLessonCard({ lesson }: { lesson: Card }) {
  const { t } = useTranslation();
  const locked = lesson.status === "locked";
  const premium = lesson.lock_reason === "PREMIUM_REQUIRED";
  const counted = lesson.competencies_total;

  return (
    <article
      className={cn(
        "flex flex-col gap-3 rounded-card bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-shadow hover:shadow-[var(--shadow-md)]",
        locked && "opacity-80",
      )}
      data-testid="lms-lesson-card"
      data-number={lesson.number}
      data-status={lesson.status}
    >
      <div className="flex items-start gap-3">
        <span
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold",
            lesson.completed ? "bg-success/15 text-success" : locked ? "bg-surface-hover text-text-muted" : "bg-accent-blue/10 text-accent-blue",
          )}
        >
          {locked ? <Lock size={16} /> : lesson.number}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {t("lms.lessonNumber", { n: lesson.number })}
          </p>
          <h3 className="font-semibold leading-snug text-text-primary">{lesson.title}</h3>
          {lesson.description && <p className="mt-1 line-clamp-2 text-sm text-text-secondary">{lesson.description}</p>}
        </div>
        <LmsStatusBadge status={lesson.status} />
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
        {lesson.has_video && (
          <span className="inline-flex items-center gap-1"><Video size={13} /> {t("lms.hasVideo")}</span>
        )}
        {lesson.duration > 0 && (
          <span className="inline-flex items-center gap-1"><Clock size={13} /> {t("lms.minutes", { n: lesson.duration })}</span>
        )}
        {counted !== null && counted > 0 && (
          <span data-testid="lms-lesson-competencies">{t("lms.competenciesDone", { done: lesson.competencies_completed ?? 0, total: counted })}</span>
        )}
        {premium && (
          <span className="inline-flex items-center gap-1 font-semibold text-warning"><Crown size={13} /> Premium</span>
        )}
      </div>

      {!locked && (
        <div>
          <div className="mb-1 flex justify-end text-xs font-bold text-accent-blue">{lesson.percent}%</div>
          <ProgressBar value={lesson.percent} trackClassName="h-1.5" />
        </div>
      )}

      {locked && lesson.lock_reason && <p className="text-xs text-text-secondary">{t(LOCK_HINT[lesson.lock_reason] ?? "lms.lockLockedHint")}</p>}

      <Link
        href={lessonHref(lesson.id)}
        className={cn(
          "mt-auto inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-opacity",
          locked ? "bg-surface-hover text-text-secondary ring-1 ring-surface-border" : "bg-accent-blue text-white hover:opacity-90",
        )}
        data-testid="lms-lesson-open"
      >
        {locked ? <Lock size={15} /> : <PlayCircle size={15} />}
        {t(locked ? "lms.whyLocked" : lesson.status === "not_started" ? "lms.start" : lesson.completed ? "lms.review" : "lms.continue")}
      </Link>
    </article>
  );
}
