import { api } from "@/lib/api";

export interface LessonSpeaking {
  id: string;
  lesson_id: string;
  title: string;
  topic: string;
  instruction: string;
  sample_answer: string | null;
  keywords: string | null;
  preparation_time: number;
  speaking_time: number;
  order_index: number;
}

// Public, published-only — Sprechen's source of truth (see
// backend/app/services/lesson_progress/section_gate.py's module
// docstring: the Assessment Engine is no longer used for this skill).
export async function getLessonSpeakings(lessonId: string): Promise<LessonSpeaking[]> {
  return api<LessonSpeaking[]>(`/api/v1/speakings/lesson/${lessonId}`);
}
