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
