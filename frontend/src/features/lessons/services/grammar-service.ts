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
export async function getLessonGrammars(lessonId: string): Promise<LessonGrammar[]> {
  return api<LessonGrammar[]>(`/api/v1/grammars/lesson/${lessonId}`);
}
