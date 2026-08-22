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
// 100-point lesson score (see LessonScoringService). percentage (0-100)
// is a quiz/exercise session's score, stored as partial credit. Called
// with no percentage from the vocabulary-learn (browsing) step — sets
// only vocabulary_completed, which is what unlocks the Wortschatz Quiz
// (see vocabulary-quiz-section.tsx); called WITH a percentage from
// vocabulary-test-section.tsx (B1+ exercises and the A1 Wortschatz
// Quiz), which sets vocabulary_score.
export async function completeLessonVocabulary(
  lessonId: string,
  percentage?: number,
): Promise<{ vocabulary_completed: boolean; vocabulary_score: number | null }> {
  return api<{ vocabulary_completed: boolean; vocabulary_score: number | null }>(
    `/api/v1/vocabularies/lesson/${lessonId}/complete`,
    percentage === undefined
      ? { method: "POST" }
      : { method: "POST", body: JSON.stringify({ percentage }) },
  );
}
