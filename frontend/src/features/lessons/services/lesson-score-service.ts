import { api } from "@/lib/api";

export interface LessonScoreComponent {
  label: string;
  points: number;
  max_points: number;
}

export interface LessonQuizResult {
  percentage: number;
  has_result: boolean;
}

export interface LessonScore {
  lesson_id: string;
  total_score: number;
  max_score: number;
  percentage: number;
  breakdown: Record<string, LessonScoreComponent>;
  feedback: string;
  strengths: string[];
  weak_areas: string[];
  lesson_quiz: LessonQuizResult;
}

// This student's own 100-point breakdown for a lesson — same access gate
// as the lesson content itself (require_lesson_access).
export async function getMyLessonScore(lessonId: string): Promise<LessonScore> {
  return api<LessonScore>(`/api/v1/lessons/${lessonId}/score`);
}
