import { api } from "@/src/services/api";

import { ADMIN_ENDPOINTS } from "../constants/endpoints";

export interface QuizGenerationQuestionType {
  template_type: string;
  label: string;
  difficulty: string;
}

export interface QuizGenerationTopic {
  topic: string;
  label: string;
  question_types: QuizGenerationQuestionType[];
}

export interface QuizGenerationTopicsResponse {
  level: string;
  topics: QuizGenerationTopic[];
}

export interface QuizGenerationRequest {
  lesson_id: string;
  quiz_id: string;
  topic: string;
  count: number;
  question_types?: string[] | null;
}

export interface QuizGenerationResponse {
  quiz_id: string;
  created_count: number;
  requested_count: number;
  shortfall: boolean;
  message: string | null;
}

/** Deterministic (no AI) quiz-question generator — see
 * app/services/quiz_generation/quiz_generation_service.py. Topics/types
 * are entirely driven by what's registered server-side (currently just
 * "Alphabet" for A1), so this list grows automatically as more topics
 * are added — nothing here is hardcoded to Alphabet. */
export async function getQuizGenerationTopics(lessonId: string): Promise<QuizGenerationTopicsResponse> {
  const response = await api.get<QuizGenerationTopicsResponse>(`${ADMIN_ENDPOINTS.quizGeneration}/topics`, {
    params: { lesson_id: lessonId },
  });
  return response.data;
}

export async function generateQuiz(data: QuizGenerationRequest): Promise<QuizGenerationResponse> {
  const response = await api.post<QuizGenerationResponse>(`${ADMIN_ENDPOINTS.quizGeneration}/generate`, data);
  return response.data;
}
