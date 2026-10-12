import { api } from "@/lib/api";

export interface LessonGrammar {
  id: string;
  lesson_id: string;
  title: string;
  /** simple HTML (sanitized server-side) or plain text */
  content: string;
  video_url: string | null;
  order_index: number;
}

// Student-facing, published-only (GET /grammars/lesson/{id}).
export async function getLessonGrammars(lessonId: string): Promise<LessonGrammar[]> {
  const data = await api<LessonGrammar[]>(`/api/v1/grammars/lesson/${lessonId}`);
  return Array.isArray(data) ? [...data].sort((a, b) => a.order_index - b.order_index) : [];
}

// Marks the Grammatik rules as read (StudentProgress.grammar_completed) —
// the completion signal of a Grammatik step without exercises.
export async function completeLessonGrammar(lessonId: string): Promise<{ grammar_completed: boolean }> {
  return api<{ grammar_completed: boolean }>(`/api/v1/grammars/lesson/${lessonId}/complete`, { method: "POST" });
}
