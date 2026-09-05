import { api } from "@/lib/api";

export interface LessonListening {
  id: string;
  lesson_id: string;
  title: string;
  audio_url: string;
  transcript: string | null;
  order_index: number;
}

// Public, published-only — Hören's source of truth (see
// backend/app/services/lesson_progress/section_gate.py's module
// docstring: the Assessment Engine is no longer used for this skill). A
// Listening row with no real audio_url yet simply isn't published, so
// it never reaches this endpoint — nothing here needs to fabricate a
// player for missing audio.
export async function getLessonListenings(lessonId: string): Promise<LessonListening[]> {
  return api<LessonListening[]>(`/api/v1/listenings/lesson/${lessonId}`);
}
