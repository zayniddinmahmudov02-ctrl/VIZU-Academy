import { api } from "@/lib/api";

export interface SectionGateEntry {
  unlocked: boolean;
  completed: boolean;
}

export type SectionGateKey =
  | "video"
  | "wortschatz"
  | "grammatik"
  | "grammatik_quiz"
  | "lesen"
  | "hoeren"
  | "schreiben"
  | "sprechen"
  | "lesson_quiz";

export type SectionGateState = Record<SectionGateKey, SectionGateEntry>;

// This student's own completion state for each of a lesson's 9 sections
// — used for progress checkmarks (nav, results, admin per-student view).
// `unlocked` is always true (sections are independently accessible in
// any order); kept in the shape for API/frontend compatibility.
export async function getSectionGate(lessonId: string): Promise<SectionGateState> {
  return api<SectionGateState>(`/api/v1/lessons/${lessonId}/section-gate`);
}
