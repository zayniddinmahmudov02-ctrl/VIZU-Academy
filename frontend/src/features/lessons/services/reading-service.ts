import { api } from "@/lib/api";

export interface LessonReading {
  id: string;
  lesson_id: string;
  title: string;
  content: string;
  order_index: number;
}

// Public, published-only — Lesen's source of truth (see
// backend/app/services/lesson_progress/section_gate.py's module
// docstring: the Assessment Engine is no longer used for this skill).
export async function getLessonReadings(lessonId: string): Promise<LessonReading[]> {
  return api<LessonReading[]>(`/api/v1/readings/lesson/${lessonId}`);
}
