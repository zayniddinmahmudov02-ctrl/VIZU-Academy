"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronDown, Lock } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import { germanLevels } from "@/constants/levels";
import { getCourses, getModules } from "@/features/courses/services/course.service";
import { useLessons } from "@/features/lessons/hooks/use-lessons";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import type { SectionGateState } from "@/features/lessons/services/section-gate-service";
import type { Lesson } from "@/features/lessons/types/lesson";
import { computeSectionProgress, isSectionDone } from "@/features/lessons/utils/section-progress";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

interface Props {
  lessonId: string;
  currentSlug: string;
  /** Closes the mobile drawer after a link is followed — no-op for the
   * always-visible desktop/tablet instance. */
  onNavigate?: () => void;
}

/** Replaces the removed bottom LessonSectionNav as the single source of
 * lesson navigation (see lessons/[lessonId]/layout.tsx). Real data only:
 * course levels (GET /courses), their one wrapping module (GET
 * /modules) and its lessons (GET /lessons, the same authenticated,
 * per-user-progress endpoint useLessons() already wrapped) — no new
 * backend endpoint, no parallel progress system. Per-activity
 * completed/applicable state for the *current* lesson reuses
 * useSectionGate exactly as the old bottom nav did (see
 * section-progress.ts). Universal across all 5 levels and every lesson
 * — nothing here branches on a specific level/lesson id. */
export default function LessonRightSidebar({ lessonId, currentSlug, onNavigate }: Props) {
  const { t } = useTranslation();

  const { data: courses } = useQuery({ queryKey: ["public-courses"], queryFn: getCourses });
  const { data: modules } = useQuery({ queryKey: ["public-modules"], queryFn: getModules });
  const { lessons, loading: lessonsLoading } = useLessons();
  const { data: gate } = useSectionGate(lessonId);

  const currentLesson = lessons.find((l) => l.id === lessonId);
  const currentModule = modules?.find((m) => m.id === currentLesson?.moduleId);
  const currentCourse = courses?.find((c) => c.id === currentModule?.course_id);
  const currentLevel = currentCourse?.level;

  const [openLevel, setOpenLevel] = useState<string | null>(null);
  useEffect(() => {
    if (currentLevel) setOpenLevel(currentLevel);
  }, [currentLevel]);

  const progress = computeSectionProgress(gate);

  const levelGroups = germanLevels.map((levelInfo) => {
    const course = courses?.find((c) => c.level === levelInfo.code);
    const courseModule = course ? modules?.find((m) => m.course_id === course.id) : undefined;
    const levelLessons = courseModule
      ? [...lessons].filter((l) => l.moduleId === courseModule.id).sort((a, b) => a.number - b.number)
      : [];
    return { levelInfo, levelLessons };
  });

  return (
    <div className="rounded-card bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      {currentLesson && (
        <div className="mb-4 border-b border-surface-border pb-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Lektion {currentLesson.number}
          </p>
          <h2 className="mt-0.5 truncate text-base font-bold text-text-primary">{currentLesson.title}</h2>

          {progress.total > 0 && (
            <div className="mt-3">
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="font-medium text-text-secondary">
                  {t("lessons.navProgress", { completed: progress.completed, total: progress.total })}
                </span>
                <span className="font-bold text-accent-blue">{progress.percentage}%</span>
              </div>
              <ProgressBar value={progress.percentage} trackClassName="h-1.5" />
            </div>
          )}
        </div>
      )}

      <nav aria-label="Kurs-Navigation" className="space-y-1.5">
        {levelGroups.map(({ levelInfo, levelLessons }) => {
          const isOpen = openLevel === levelInfo.code;
          return (
            <div key={levelInfo.code} className="overflow-hidden rounded-xl ring-1 ring-surface-border">
              <button
                type="button"
                onClick={() => setOpenLevel(isOpen ? null : levelInfo.code)}
                aria-expanded={isOpen}
                className="flex min-h-11 w-full items-center justify-between gap-2 bg-surface-hover/60 px-3.5 py-3 text-left text-sm font-bold text-text-primary transition-colors hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/50"
              >
                {t(levelInfo.labelKey)}
                <ChevronDown
                  size={16}
                  className={cn("shrink-0 text-text-muted transition-transform duration-200", isOpen && "rotate-180")}
                />
              </button>

              {isOpen && (
                <div className="space-y-1 p-1.5">
                  {lessonsLoading && <p className="px-2 py-2 text-xs text-text-muted">{t("common.loading")}</p>}

                  {!lessonsLoading && levelLessons.length === 0 && (
                    <p className="px-2 py-2 text-xs text-text-muted">Keine Lektionen verfügbar.</p>
                  )}

                  {levelLessons.map((lesson) => (
                    <LessonAccordionItem
                      key={lesson.id}
                      lesson={lesson}
                      isCurrent={lesson.id === lessonId}
                      currentSlug={currentSlug}
                      gate={lesson.id === lessonId ? gate : undefined}
                      onNavigate={onNavigate}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>
    </div>
  );
}

function LessonAccordionItem({
  lesson,
  isCurrent,
  currentSlug,
  gate,
  onNavigate,
}: {
  lesson: Lesson;
  isCurrent: boolean;
  currentSlug: string;
  gate: SectionGateState | undefined;
  onNavigate?: () => void;
}) {
  const { t } = useTranslation();
  const href = lesson.isLocked ? "/vizu-pay" : `/lessons/${lesson.id}`;
  const completed = lesson.progress >= 100;

  return (
    <div className={cn("rounded-lg", isCurrent && "bg-accent-blue/5 ring-1 ring-accent-blue/20")}>
      <Link
        href={href}
        aria-current={isCurrent ? "page" : undefined}
        onClick={onNavigate}
        className={cn(
          "flex min-h-11 items-center gap-2.5 rounded-lg px-2.5 py-2.5 text-sm transition-colors hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/50",
          isCurrent ? "font-bold text-accent-blue" : "font-medium text-text-primary",
        )}
      >
        <span
          className={cn(
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold",
            lesson.isLocked
              ? "bg-surface-hover text-text-muted"
              : completed
                ? "bg-success/15 text-success"
                : isCurrent
                  ? "bg-accent-blue text-white"
                  : "bg-surface-hover text-text-muted",
          )}
        >
          {lesson.isLocked ? <Lock size={11} /> : completed ? <Check size={13} /> : lesson.number}
        </span>
        <span className="min-w-0 flex-1 truncate">{lesson.title}</span>
      </Link>

      {isCurrent && !lesson.isLocked && (
        <div className="space-y-0.5 px-1.5 pb-2 pl-8">
          {computeSectionProgress(gate).visibleSections.map((section) => {
            const active = section.slug === currentSlug;
            const done = isSectionDone(section, gate);
            return (
              <Link
                key={section.slug}
                href={`/lessons/${lesson.id}/${section.slug}`}
                aria-current={active ? "page" : undefined}
                onClick={onNavigate}
                className={cn(
                  "flex min-h-11 items-center gap-2 rounded-md px-2.5 py-2 text-[13px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/50",
                  active
                    ? "bg-accent-blue text-white shadow-sm"
                    : done
                      ? "text-success hover:bg-surface-hover"
                      : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
                )}
              >
                {done ? (
                  <Check size={13} className={active ? "text-white" : "text-success"} />
                ) : (
                  <span aria-hidden="true">{section.emoji}</span>
                )}
                <span className="truncate">{t(section.titleKey)}</span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
