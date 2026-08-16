import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { LessonScoreShape } from "@/components/lesson-player/results/lesson-score-breakdown";
import type { SectionGateState } from "@/features/lessons/services/section-gate-service";

export async function getStudentLessonScore(lessonId: string, userId: string): Promise<LessonScoreShape> {
  const response = await api.get<LessonScoreShape>(
    `${ADMIN_ENDPOINTS.lessons}/${lessonId}/students/${userId}/score`,
  );
  return response.data;
}

export async function getStudentSectionGate(lessonId: string, userId: string): Promise<SectionGateState> {
  const response = await api.get<SectionGateState>(
    `${ADMIN_ENDPOINTS.lessons}/${lessonId}/students/${userId}/section-gate`,
  );
  return response.data;
}
