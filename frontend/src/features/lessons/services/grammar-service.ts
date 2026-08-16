import { api } from "@/lib/api";

export interface LessonGrammar {
  id: string;
  lesson_id: string;
  title: string;
  content: string;
  video_url: string | null;
  order_index: number;
}

// Public — requires login (matches the lesson content-access pattern used
// by GET /lessons/{id} and GET /vocabularies/lesson/{id}), published-only.
// Gated server-side behind Wortschatz completion (sequential progression).
export async function getLessonGrammars(lessonId: string): Promise<LessonGrammar[]> {
  return api<LessonGrammar[]>(`/api/v1/grammars/lesson/${lessonId}`);
}

// Marks Grammatik viewed — unlocks Grammatik Quiz next in the sequence.
export async function completeLessonGrammar(lessonId: string): Promise<{ grammar_completed: boolean }> {
  return api<{ grammar_completed: boolean }>(`/api/v1/grammars/lesson/${lessonId}/complete`, {
    method: "POST",
  });
}
