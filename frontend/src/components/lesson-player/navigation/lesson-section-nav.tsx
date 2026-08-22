"use client";

import Link from "next/link";
import { Check, ChevronLeft, ChevronRight, Lock } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import ProgressBar from "@/components/ui/progress-bar";
import { SECTION_GATE_KEYS, getSectionIndex, lessonSections, type LessonSectionMeta } from "@/constants/lesson-sections";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import type { SectionGateState } from "@/features/lessons/services/section-gate-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

interface Props {
  lessonId: string;
  currentSlug: string;
}

/** A section counts toward the checklist only if it has a real
 * completion concept (a gate key) and this lesson actually has that
 * content — matches backend/app/services/lesson_progress/
 * section_gate.py exactly: homework/results have no gate key at all,
 * and e.g. Wortschatz Quiz is never applicable for B1-C1. While the
 * gate is still loading, a section is treated as applicable so the bar
 * doesn't flicker empty-then-full. */
function isVisible(section: LessonSectionMeta, gate: SectionGateState | undefined): boolean {
  const key = SECTION_GATE_KEYS[section.type];
  if (!key) return true;
  return gate ? gate[key].applicable : true;
}

function isUnlocked(section: LessonSectionMeta, gate: SectionGateState | undefined): boolean {
  const key = SECTION_GATE_KEYS[section.type];
  if (!key || !gate) return true;
  return gate[key].unlocked;
}

function isDone(section: LessonSectionMeta, gate: SectionGateState | undefined): boolean {
  const key = SECTION_GATE_KEYS[section.type];
  if (!key || !gate) return false;
  return gate[key].completed;
}

/** Real, server-derived progress/lock state — no manual "mark complete"
 * control exists anywhere in this component; every checkmark and lock
 * icon reflects actual student work (see useSectionGate). */
export default function LessonSectionNav({ lessonId, currentSlug }: Props) {
  const { t } = useTranslation();
  const { data: gate } = useSectionGate(lessonId);

  const visibleSections = lessonSections.filter((section) => isVisible(section, gate));
  const trackedSections = visibleSections.filter((section) => SECTION_GATE_KEYS[section.type] !== null);
  const completedCount = trackedSections.filter((section) => isDone(section, gate)).length;
  const total = trackedSections.length;

  const currentIndex = getSectionIndex(currentSlug);
  const visibleIndex = visibleSections.findIndex((section) => section.slug === currentSlug);
  const prevSection = visibleIndex > 0 ? visibleSections[visibleIndex - 1] : null;
  const nextSection = visibleIndex >= 0 && visibleIndex < visibleSections.length - 1 ? visibleSections[visibleIndex + 1] : null;
  const nextUnlocked = nextSection ? isUnlocked(nextSection, gate) : false;

  return (
    <div className="mt-8 space-y-5 sm:mt-10">
      {/* Progress */}
      {total > 0 && (
        <div>
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium text-text-secondary">
              {t("lessons.navProgress", { completed: completedCount, total })}
            </span>
            <span className="font-bold text-accent-blue">{Math.round((completedCount / total) * 100)}%</span>
          </div>
          <ProgressBar value={(completedCount / total) * 100} trackClassName="h-2" />
        </div>
      )}

      {/* Horizontal section bar — only sections this lesson actually has;
          locked ones are shown but not clickable. */}
      <div className="flex gap-2 overflow-x-auto rounded-card bg-surface-card p-2 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        {visibleSections.map((section) => {
          const active = section.slug === currentSlug;
          const done = isDone(section, gate);
          const unlocked = isUnlocked(section, gate);

          const content = (
            <>
              <span aria-hidden="true">{unlocked ? section.emoji : "🔒"}</span>
              {t(section.titleKey)}
              {done && <Check size={14} className={active ? "text-white" : "text-success"} />}
            </>
          );

          if (!unlocked) {
            return (
              <span
                key={section.slug}
                aria-disabled="true"
                className="relative flex shrink-0 cursor-not-allowed items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-text-muted opacity-60"
              >
                {content}
              </span>
            );
          }

          return (
            <Link
              key={section.slug}
              href={`/lessons/${lessonId}/${section.slug}`}
              aria-current={active ? "page" : undefined}
              prefetch={false}
              className={`relative flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors duration-200 ${
                active
                  ? "bg-gradient-to-r from-accent-blue to-purple-600 text-white shadow-md shadow-accent-blue/25"
                  : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
              }`}
            >
              {content}
            </Link>
          );
        })}
      </div>

      {/* Previous / Next — no manual completion control */}
      <div className="flex flex-col-reverse items-center gap-3 border-t border-surface-border pt-6 sm:flex-row sm:justify-between">
        {prevSection ? (
          <Link
            href={`/lessons/${lessonId}/${prevSection.slug}`}
            className={cn(buttonVariants({ variant: "secondary", size: "sm" }), "w-full sm:w-auto")}
          >
            <ChevronLeft size={16} />
            {t("lessons.navPrevious")}
          </Link>
        ) : (
          <span className="hidden sm:block" />
        )}

        {nextSection && nextUnlocked ? (
          <Link
            href={`/lessons/${lessonId}/${nextSection.slug}`}
            className={cn(buttonVariants({ variant: "primary", size: "sm" }), "w-full sm:w-auto")}
          >
            {t("lessons.navNext")}
            <ChevronRight size={16} />
          </Link>
        ) : nextSection ? (
          <span
            aria-disabled="true"
            className={cn(
              buttonVariants({ variant: "primary", size: "sm" }),
              "w-full cursor-not-allowed opacity-50 sm:w-auto",
            )}
          >
            <Lock size={14} />
            {t("lessons.navNext")}
          </span>
        ) : (
          <span className="hidden sm:block" />
        )}
      </div>
    </div>
  );
}
