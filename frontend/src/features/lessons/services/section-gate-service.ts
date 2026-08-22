import { api } from "@/lib/api";

export interface SectionGateEntry {
  unlocked: boolean;
  completed: boolean;
  /** Does this lesson actually have this kind of content at all? A
   * section a lesson doesn't have never blocks and is never required
   * for lesson completion — see backend/app/services/lesson_progress/
   * section_gate.py, the single source of truth this mirrors. */
  applicable: boolean;
}

export type SectionGateKey =
  | "video"
  | "wortschatz"
  | "wortschatz_quiz"
  | "grammatik"
  | "grammatik_quiz"
  | "lesen"
  | "hoeren"
  | "schreiben"
  | "sprechen"
  | "lesson_quiz";

export type SectionGateState = Record<SectionGateKey, SectionGateEntry>;

// This student's own completion state for each of a lesson's sections
// — real, server-computed sequential gating (a section unlocks once
// every applicable section before it, in the fixed order, is
// completed) and the source of truth for the nav's checkmarks/locks.
export async function getSectionGate(lessonId: string): Promise<SectionGateState> {
  return api<SectionGateState>(`/api/v1/lessons/${lessonId}/section-gate`);
}

/** Lesson completed = every applicable, gated section is completed
 * ("grammatik" is never gated/required — see section_gate.py). Derived
 * client-side from the same state the nav already fetches, rather than
 * a separate endpoint. */
export function isLessonComplete(gate: SectionGateState): boolean {
  return (Object.keys(gate) as SectionGateKey[])
    .filter((key) => key !== "grammatik")
    .every((key) => !gate[key].applicable || gate[key].completed);
}
