import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { LessonScoreShape } from "@/components/lesson-player/results/lesson-score-breakdown";

export async function getStudentLessonScore(lessonId: string, userId: string): Promise<LessonScoreShape> {
  const response = await api.get<LessonScoreShape>(
    `${ADMIN_ENDPOINTS.lessons}/${lessonId}/students/${userId}/score`,
  );
  return response.data;
}
