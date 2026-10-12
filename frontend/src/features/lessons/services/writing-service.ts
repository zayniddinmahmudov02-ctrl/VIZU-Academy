import { api } from "@/lib/api";

export interface LessonWriting {
  id: string;
  lesson_id: string;
  title: string;
  instruction: string;
  min_words: number;
  max_words: number;
  order_index: number;
  ai_evaluation_enabled?: boolean;
  max_attempts?: number;
  max_score?: number;
  helper_words?: string | null;
  image_url?: string | null;
  opens_at?: string | null;
  closes_at?: string | null;
  text_type?: "message" | "email" | "letter" | "description" | "opinion" | "essay" | "report" | "other" | null;
  audience?: string | null;
  time_limit_minutes?: number | null;
}

// Public, published-only — Schreiben's source of truth (see
// backend/app/services/lesson_progress/section_gate.py's module
// docstring: the Assessment Engine is no longer used for this skill).
export async function getLessonWritings(lessonId: string): Promise<LessonWriting[]> {
  return api<LessonWriting[]>(`/api/v1/writings/lesson/${lessonId}`);
}
