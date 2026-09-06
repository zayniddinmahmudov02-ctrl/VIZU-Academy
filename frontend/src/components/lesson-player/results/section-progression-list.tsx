import { Check, Circle } from "lucide-react";

import type { SectionGateState } from "@/features/lessons/services/section-gate-service";

const LABELS: Record<keyof SectionGateState, string> = {
  video: "Video",
  wortschatz: "Wortschatz",
  wortschatz_quiz: "Wortschatz Quiz",
  grammatik: "Grammatik",
  grammatik_quiz: "Grammatik Quiz",
  lesen: "Lesen",
  hoeren: "Hören",
  schreiben: "Schreiben",
  sprechen: "Sprechen",
  lesson_quiz: "Lesson Quiz",
};

// Standalone "grammatik" is deliberately excluded — it's no longer a
// student-facing lesson step (grammar is taught inside the Video;
// Grammatik Quiz is the only grammar step left). The backend still
// returns a "grammatik" entry in SectionGateState (kept for other
// internal consumers), so it stays in LABELS above for type-correctness,
// it's just never rendered here.
//
// Every other key is only rendered when the lesson actually has that
// content (entry.applicable) — e.g. "wortschatz_quiz" only shows for A1
// lessons, which have a real VOCABULARY quiz; B1-C1 lessons don't render
// it at all, same real data the right sidebar now uses (see
// lesson-right-sidebar.tsx / section-progress.ts).
const ORDER: (keyof SectionGateState)[] = [
  "video",
  "wortschatz",
  "wortschatz_quiz",
  "grammatik_quiz",
  "lesen",
  "hoeren",
  "schreiben",
  "sprechen",
  "lesson_quiz",
];

/** Shared per-section completion checklist — every section is
 * independently accessible, so this only shows done/not-done, not a
 * lock state. Used by both the student's own results view and the
 * admin's per-student progression view. */
export default function SectionProgressionList({ gate }: { gate: SectionGateState }) {
  return (
    <div className="space-y-1.5">
      {ORDER.filter((key) => gate[key].applicable).map((key) => {
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
              {LABELS[key]}
            </span>
            <span className="text-xs text-text-muted">{label}</span>
          </div>
        );
      })}
    </div>
  );
}
