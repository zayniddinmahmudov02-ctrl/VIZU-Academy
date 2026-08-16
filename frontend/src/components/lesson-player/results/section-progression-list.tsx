import { Check, Lock, Unlock } from "lucide-react";

import type { SectionGateState } from "@/features/lessons/services/section-gate-service";

const LABELS: Record<keyof SectionGateState, string> = {
  video: "Video",
  wortschatz: "Wortschatz",
  grammatik: "Grammatik",
  grammatik_quiz: "Grammatik Quiz",
  lesen: "Lesen",
  hoeren: "Hören",
  schreiben: "Schreiben",
  sprechen: "Sprechen",
  lesson_quiz: "Lesson Quiz",
};

const ORDER: (keyof SectionGateState)[] = [
  "video",
  "wortschatz",
  "grammatik",
  "grammatik_quiz",
  "lesen",
  "hoeren",
  "schreiben",
  "sprechen",
  "lesson_quiz",
];

/** Shared "sequential learning path" checklist — used by both the
 * student's own view (implicitly, via the lock icons in
 * LessonSectionNav) and the admin's per-student progression view. */
export default function SectionProgressionList({ gate }: { gate: SectionGateState }) {
  return (
    <div className="space-y-1.5">
      {ORDER.map((key) => {
        const entry = gate[key];
        const icon = entry.completed ? (
          <Check size={14} className="text-success" />
        ) : entry.unlocked ? (
          <Unlock size={14} className="text-warning" />
        ) : (
          <Lock size={14} className="text-text-muted" />
        );
        const label = entry.completed ? "Abgeschlossen" : entry.unlocked ? "Offen" : "Gesperrt";

        return (
          <div key={key} className="flex items-center justify-between rounded-lg bg-surface-hover/40 px-3 py-2 text-sm">
            <span className="flex items-center gap-2 text-text-primary">
              {icon}
              {LABELS[key]}
            </span>
            <span className="text-xs text-text-muted">{label}</span>
          </div>
        );
      })}
    </div>
  );
}
