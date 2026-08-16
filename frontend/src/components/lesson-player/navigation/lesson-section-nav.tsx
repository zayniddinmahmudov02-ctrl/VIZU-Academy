"use client";

import Link from "next/link";
import { Check, CheckCircle2, ChevronLeft, ChevronRight, Lock } from "lucide-react";

import Button, { buttonVariants } from "@/components/ui/button";
import ProgressBar from "@/components/ui/progress-bar";
import { getSectionIndex, lessonSections, SECTION_GATE_KEYS } from "@/constants/lesson-sections";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { useLessonProgressStore } from "@/store/lesson-progress-store";

interface Props {
  lessonId: string;
  currentSlug: string;
}

/** Stable fallback reference — a fresh `[]` on every selector call would make
 *  useSyncExternalStore see a "changed" snapshot on every render and loop forever. */
const EMPTY_COMPLETED: string[] = [];

export default function LessonSectionNav({ lessonId, currentSlug }: Props) {
  const { t } = useTranslation();
  const completedSections = useLessonProgressStore(
    (state) => state.completedSections[lessonId] ?? EMPTY_COMPLETED,
  );
  const toggleSection = useLessonProgressStore((state) => state.toggleSection);
  const { data: gate } = useSectionGate(lessonId);

  const currentIndex = getSectionIndex(currentSlug);
  const total = lessonSections.length;
  const completedCount = completedSections.length;
  const isCurrentComplete = completedSections.includes(currentSlug);

  const prevSection = currentIndex > 0 ? lessonSections[currentIndex - 1] : null;
  const nextSection = currentIndex < total - 1 ? lessonSections[currentIndex + 1] : null;

  function isUnlocked(sectionType: (typeof lessonSections)[number]["type"]): boolean {
    const gateKey = SECTION_GATE_KEYS[sectionType];
    if (gateKey === null) return true; // not sequentially gated (e.g. Hausaufgabe, Ergebnis)
    if (!gate) return true; // still loading — don't flash every tab as locked
    return gate[gateKey].unlocked;
  }

  return (
    <div className="mt-8 space-y-5 sm:mt-10">
      {/* Progress */}
      <div>
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="font-medium text-text-secondary">
            {t("lessons.navProgress", { completed: completedCount, total })}
          </span>
          <span className="font-bold text-accent-blue">
            {Math.round((completedCount / total) * 100)}%
          </span>
        </div>
        <ProgressBar value={(completedCount / total) * 100} trackClassName="h-2" />
      </div>

      {/* Horizontal section bar — locked sections show a lock icon and
          aren't clickable, mirroring what the backend independently
          enforces on the underlying content endpoints. */}
      <div className="flex gap-2 overflow-x-auto rounded-card bg-surface-card p-2 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        {lessonSections.map((section) => {
          const active = section.slug === currentSlug;
          const done = completedSections.includes(section.slug);
          const unlocked = isUnlocked(section.type);

          if (!unlocked) {
            return (
              <span
                key={section.slug}
                aria-disabled="true"
                title={t("lessons.sectionLockedHint")}
                className="relative flex shrink-0 cursor-not-allowed items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-text-muted/60"
              >
                <Lock size={13} aria-hidden="true" />
                {t(section.titleKey)}
              </span>
            );
          }

          return (
            <Link
              key={section.slug}
              href={`/lessons/${lessonId}/${section.slug}`}
              aria-current={active ? "page" : undefined}
              className={`relative flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors duration-200 ${
                active
                  ? "bg-gradient-to-r from-accent-blue to-purple-600 text-white shadow-md shadow-accent-blue/25"
                  : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
              }`}
            >
              <span aria-hidden="true">{section.emoji}</span>
              {t(section.titleKey)}
              {done && <Check size={14} className={active ? "text-white" : "text-success"} />}
            </Link>
          );
        })}
      </div>

      {/* Previous / Mark complete / Next */}
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

        <Button
          type="button"
          variant={isCurrentComplete ? "secondary" : "primary"}
          size="sm"
          onClick={() => toggleSection(lessonId, currentSlug)}
          className="w-full sm:w-auto"
        >
          <CheckCircle2 size={16} className={isCurrentComplete ? "text-success" : ""} />
          {isCurrentComplete ? t("lessons.navCompleted") : t("lessons.navMarkComplete")}
        </Button>

        {nextSection && isUnlocked(nextSection.type) ? (
          <Link
            href={`/lessons/${lessonId}/${nextSection.slug}`}
            className={cn(buttonVariants({ variant: "primary", size: "sm" }), "w-full sm:w-auto")}
          >
            {t("lessons.navNext")}
            <ChevronRight size={16} />
          </Link>
        ) : nextSection ? (
          <span
            title={t("lessons.sectionLockedHint")}
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
