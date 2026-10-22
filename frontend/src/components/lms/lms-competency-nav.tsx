"use client";

import Link from "next/link";
import { CheckCircle2, CircleDashed, Lock, PlayCircle } from "lucide-react";

import { COMPETENCY_META, competencyHref, videoHref } from "@/features/lms/competencies";
import type { CompetencyKind, LmsCompetency } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

/** The lesson's competencies in the backend's order (position), preceded by
 * Video-Unterricht. Vertical on large screens, a horizontally scrollable
 * strip on phones. "Nicht verfügbar" items are shown but not clickable. */
export default function LmsCompetencyNav({ lessonId, competencies, current, videoActive = false, videoCount = 0 }: {
  lessonId: string; competencies: LmsCompetency[]; current?: CompetencyKind; videoActive?: boolean; videoCount?: number;
}) {
  const { t } = useTranslation();
  const ordered = [...competencies].sort((a, b) => a.position - b.position);

  return (
    <nav aria-label={t("lms.competencies")} data-testid="lms-competency-nav">
      <ol className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1 lg:mx-0 lg:flex-col lg:overflow-visible lg:px-0 lg:pb-0">
        <li data-kind="VIDEO" data-testid="lms-nav-video">
          <Link href={videoHref(lessonId)} aria-current={videoActive ? "page" : undefined}
                className={cn(
                  "flex min-h-11 shrink-0 items-center gap-2 rounded-xl px-2.5 py-2 text-sm font-medium transition-colors lg:w-full",
                  videoActive ? "bg-accent-blue text-white shadow-sm" : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
                )}>
            <span className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-lg", videoActive ? "bg-white/20 text-white" : "bg-surface-hover text-text-muted")}>
              <PlayCircle size={15} />
            </span>
            <span className="truncate">{t("lms.videoLesson")}</span>
            {videoCount > 0 && <span className={cn("ml-auto shrink-0 text-xs", videoActive ? "text-white/80" : "text-text-muted")}>{videoCount}</span>}
          </Link>
        </li>
        {ordered.map((c) => {
          const meta = COMPETENCY_META[c.kind];
          const Icon = meta.icon;
          const active = c.kind === current;
          const disabled = c.status === "not_available";
          const inner = (
            <>
              <span className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold",
                active ? "bg-white/20 text-white" : c.status === "completed" ? "bg-success/15 text-success" : "bg-surface-hover text-text-muted")}>
                {c.status === "completed" ? <CheckCircle2 size={15} /> : c.position}
              </span>
              <Icon size={15} className="hidden shrink-0 sm:block" aria-hidden="true" />
              <span className="truncate">{meta.name}</span>
              {c.status === "locked" && <Lock size={13} className="ml-auto shrink-0" aria-label={t("lms.statusLocked")} />}
              {disabled && <CircleDashed size={13} className="ml-auto shrink-0" aria-label={t("lms.statusNotAvailable")} />}
            </>
          );
          const cls = cn(
            "flex min-h-11 shrink-0 items-center gap-2 rounded-xl px-2.5 py-2 text-sm font-medium transition-colors lg:w-full",
            active ? "bg-accent-blue text-white shadow-sm" : disabled ? "text-text-muted opacity-70" : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
          );
          return (
            <li key={c.kind} data-kind={c.kind} data-status={c.status}>
              {disabled ? (
                <span className={cls} aria-disabled="true" title={t("lms.statusNotAvailable")}>{inner}</span>
              ) : (
                <Link
                  href={competencyHref(lessonId, c.kind)}
                  aria-current={active ? "page" : undefined}
                  aria-label={c.status === "completed" ? `${meta.name}: ${t("lms.statusCompleted")}` : undefined}
                  className={cls}
                >
                  {inner}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
