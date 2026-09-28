"use client";

import { Check, Circle } from "lucide-react";

import { COMPLETION_TRACKED_GATE_KEYS } from "@/constants/lesson-sections";
import type { SectionGateKey, SectionGateState } from "@/features/lessons/services/section-gate-service";
import { useTranslation } from "@/lib/i18n/use-translation";

const LABEL_KEYS: Partial<Record<SectionGateKey, string>> = {
  video: "lessons.sectionVideo",
  schreiben: "lessons.sectionWriting",
  sprechen: "lessons.sectionSpeaking",
  wortschatz_quiz: "lessons.sectionVocabularyQuiz",
  lesson_quiz: "lessons.sectionLessonQuiz",
};

// Only the steps that have a real completion signal are listed (the same
// set the backend requires for a completed lesson — see COMPLETION_
// TRACKED_GATE_KEYS); Lesen/Hören are passage/audio only and the removed
// Wortschatz-browsing/Grammatik steps no longer exist for students. A
// section is only rendered when the lesson actually has that content
// (entry.applicable).
/** Shared per-section completion checklist — every section is
 * independently accessible, so this only shows done/not-done, not a
 * lock state. Used by both the student's own results view and the
 * admin's per-student progression view. */
export default function SectionProgressionList({ gate }: { gate: SectionGateState }) {
  const { t } = useTranslation();

  return (
    <div className="space-y-1.5">
      {COMPLETION_TRACKED_GATE_KEYS.filter((key) => gate[key].applicable).map((key) => {
        const entry = gate[key];
        const icon = entry.completed ? (
          <Check size={14} className="text-success" />
        ) : (
          <Circle size={14} className="text-text-muted" />
        );
        const label = entry.completed ? "Abgeschlossen" : "Offen";

        return (
          <div key={key} className="flex items-center justify-between rounded-lg bg-surface-hover/40 px-3 py-2 text-sm">
            <span className="flex items-center gap-2 text-text-primary">
              {icon}
              {t(LABEL_KEYS[key] ?? key)}
            </span>
            <span className="text-xs text-text-muted">{label}</span>
          </div>
        );
      })}
    </div>
  );
}
