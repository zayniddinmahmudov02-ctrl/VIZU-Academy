import { api } from "@/lib/api";

export interface LessonWriting {
  id: string;
  lesson_id: string;
  title: string;
  instruction: string;
  min_words: number;
  max_words: number;
  order_index: number;
}

// Public, published-only — Schreiben's source of truth (see
// backend/app/services/lesson_progress/section_gate.py's module
// docstring: the Assessment Engine is no longer used for this skill).
export async function getLessonWritings(lessonId: string): Promise<LessonWriting[]> {
  return api<LessonWriting[]>(`/api/v1/writings/lesson/${lessonId}`);
}
