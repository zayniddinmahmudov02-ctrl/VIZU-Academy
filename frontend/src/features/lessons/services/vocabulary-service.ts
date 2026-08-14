import { api } from "@/lib/api";

export interface LessonVocabularyItem {
  id: string;
  lesson_id: string;
  german_word: string;
  article: string | null;
  plural: string | null;
  translation: string;
  example_sentence: string | null;
  example_translation: string | null;
  audio_url: string | null;
  image_url: string | null;
  order_index: number;
}

// Public — requires the lesson's video to be completed first (enforced
// server-side via require_video_completed), published-only.
export async function getLessonVocabularies(lessonId: string): Promise<LessonVocabularyItem[]> {
  return api<LessonVocabularyItem[]>(`/api/v1/vocabularies/lesson/${lessonId}`);
}

// Marks Wortschatz reviewed — feeds the Wortschatz component of the
// 100-point lesson score (see LessonScoringService).
export async function completeLessonVocabulary(lessonId: string): Promise<{ vocabulary_completed: boolean }> {
  return api<{ vocabulary_completed: boolean }>(`/api/v1/vocabularies/lesson/${lessonId}/complete`, {
    method: "POST",
  });
}
