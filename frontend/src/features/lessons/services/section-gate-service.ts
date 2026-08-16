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

// This student's own unlock/completion state for all 9 sequential
// sections of a lesson — the real gate lives server-side on each
// content endpoint; this is just what the UI renders lock icons from.
export async function getSectionGate(lessonId: string): Promise<SectionGateState> {
  return api<SectionGateState>(`/api/v1/lessons/${lessonId}/section-gate`);
}
