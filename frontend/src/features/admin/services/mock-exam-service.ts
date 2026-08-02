import { api } from "@/src/services/api";
import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  CertificationProvider,
  CertificationProviderCreate,
  CertificationProviderUpdate,
  CertificationProviderAnalytics,
  DashboardSummary,
  Kompetenz,
  KompetenzCreate,
  KompetenzUpdate,
  ListeningContent,
  ListeningContentCreate,
  ListeningContentUpdate,
  MockExamLevel,
  MockExamLevelCreate,
  MockExamLevelUpdate,
  MockQuestion,
  MockQuestionCreate,
  MockQuestionMoveRequest,
  MockQuestionOption,
  MockQuestionOptionCreate,
  MockQuestionOptionUpdate,
  MockQuestionUpdate,
  MockSpeakingSubmission,
  MockSpeakingSubmissionTeacherUpdate,
  MockTestAttempt,
  MockWritingSubmission,
  MockWritingSubmissionTeacherUpdate,
  ModelTest,
  ModelTestAnalytics,
  ModelTestCreate,
  ModelTestScore,
  ModelTestUpdate,
  ReadingContent,
  ReadingContentCreate,
  ReadingContentUpdate,
  SpeakingTask,
  SpeakingTaskCreate,
  SpeakingTaskUpdate,
  Teil,
  TeilCreate,
  TeilUpdate,
  WritingTask,
  WritingTaskCreate,
  WritingTaskUpdate,
} from "../types/mock-exam.types";

// ============================================================
// Hierarchy: Certificates -> Levels -> Model Tests -> Kompetenzen -> Teile
// ============================================================

export const mockExamProvidersApi = createCrudApi<
  CertificationProvider,
  CertificationProviderCreate,
  CertificationProviderUpdate
>(ADMIN_ENDPOINTS.mockExamProviders);

export const mockExamLevelsApi = createCrudApi<MockExamLevel, MockExamLevelCreate, MockExamLevelUpdate>(
  ADMIN_ENDPOINTS.mockExamLevels,
);

export const mockExamModelTestsApi = createCrudApi<ModelTest, ModelTestCreate, ModelTestUpdate>(
  ADMIN_ENDPOINTS.mockExamModelTests,
);

export const mockExamKompetenzenApi = createCrudApi<Kompetenz, KompetenzCreate, KompetenzUpdate>(
  ADMIN_ENDPOINTS.mockExamKompetenzen,
);

export const mockExamTeileApi = createCrudApi<Teil, TeilCreate, TeilUpdate>(ADMIN_ENDPOINTS.mockExamTeile);

export async function getModelTestScore(modelTestId: string): Promise<ModelTestScore> {
  const response = await api.get<ModelTestScore>(ADMIN_ENDPOINTS.mockExamModelTestScore(modelTestId));
  return response.data;
}

// ============================================================
// Content (Reading / Listening / Writing / Speaking) — 1:1 with a Teil
// ============================================================

export const mockExamReadingContentApi = createCrudApi<
  ReadingContent,
  ReadingContentCreate,
  ReadingContentUpdate
>(ADMIN_ENDPOINTS.mockExamReadingContent);

export const mockExamListeningContentApi = createCrudApi<
  ListeningContent,
  ListeningContentCreate,
  ListeningContentUpdate
>(ADMIN_ENDPOINTS.mockExamListeningContent);

export const mockExamWritingTasksApi = createCrudApi<WritingTask, WritingTaskCreate, WritingTaskUpdate>(
  ADMIN_ENDPOINTS.mockExamWritingTasks,
);

export const mockExamSpeakingTasksApi = createCrudApi<SpeakingTask, SpeakingTaskCreate, SpeakingTaskUpdate>(
  ADMIN_ENDPOINTS.mockExamSpeakingTasks,
);

async function getOrNull<T>(url: string): Promise<T | null> {
  const response = await api.get<T | null>(url);
  return response.data ?? null;
}

export const getReadingContentByTeil = (teilId: string) =>
  getOrNull<ReadingContent>(ADMIN_ENDPOINTS.mockExamReadingContentByTeil(teilId));
export const getListeningContentByTeil = (teilId: string) =>
  getOrNull<ListeningContent>(ADMIN_ENDPOINTS.mockExamListeningContentByTeil(teilId));
export const getWritingTaskByTeil = (teilId: string) =>
  getOrNull<WritingTask>(ADMIN_ENDPOINTS.mockExamWritingTaskByTeil(teilId));
export const getSpeakingTaskByTeil = (teilId: string) =>
  getOrNull<SpeakingTask>(ADMIN_ENDPOINTS.mockExamSpeakingTaskByTeil(teilId));

// ============================================================
// Questions (Question Bank) + Options
// ============================================================

export const mockExamQuestionsApi = createCrudApi<MockQuestion, MockQuestionCreate, MockQuestionUpdate>(
  ADMIN_ENDPOINTS.mockExamQuestions,
);

export const mockExamQuestionOptionsApi = createCrudApi<
  MockQuestionOption,
  MockQuestionOptionCreate,
  MockQuestionOptionUpdate
>(ADMIN_ENDPOINTS.mockExamQuestionOptions);

export async function listQuestions(params: {
  reading_content_id?: string;
  listening_content_id?: string;
}): Promise<MockQuestion[]> {
  const response = await api.get<MockQuestion[]>(ADMIN_ENDPOINTS.mockExamQuestions, { params });
  return response.data;
}

export async function duplicateQuestion(questionId: string): Promise<MockQuestion> {
  const response = await api.post<MockQuestion>(ADMIN_ENDPOINTS.mockExamQuestionDuplicate(questionId));
  return response.data;
}

export async function moveQuestion(
  questionId: string,
  data: MockQuestionMoveRequest,
): Promise<MockQuestion> {
  const response = await api.post<MockQuestion>(ADMIN_ENDPOINTS.mockExamQuestionMove(questionId), data);
  return response.data;
}

// ============================================================
// Student Attempts / Results / AI Evaluation
// ============================================================

export async function listAttempts(params?: {
  model_test_id?: string;
  user_id?: string;
}): Promise<MockTestAttempt[]> {
  const response = await api.get<MockTestAttempt[]>(ADMIN_ENDPOINTS.mockExamAttempts, { params });
  return response.data;
}

export async function listWritingSubmissions(attemptId?: string): Promise<MockWritingSubmission[]> {
  const response = await api.get<MockWritingSubmission[]>(ADMIN_ENDPOINTS.mockExamWritingSubmissions, {
    params: attemptId ? { attempt_id: attemptId } : undefined,
  });
  return response.data;
}

export async function evaluateWritingSubmission(id: string): Promise<MockWritingSubmission> {
  const response = await api.post<MockWritingSubmission>(ADMIN_ENDPOINTS.mockExamWritingSubmissionAiEvaluate(id));
  return response.data;
}

export async function reviewWritingSubmission(
  id: string,
  data: MockWritingSubmissionTeacherUpdate,
): Promise<MockWritingSubmission> {
  const response = await api.put<MockWritingSubmission>(ADMIN_ENDPOINTS.mockExamWritingSubmissionReview(id), data);
  return response.data;
}

export async function listSpeakingSubmissions(attemptId?: string): Promise<MockSpeakingSubmission[]> {
  const response = await api.get<MockSpeakingSubmission[]>(ADMIN_ENDPOINTS.mockExamSpeakingSubmissions, {
    params: attemptId ? { attempt_id: attemptId } : undefined,
  });
  return response.data;
}

export async function evaluateSpeakingSubmission(id: string): Promise<MockSpeakingSubmission> {
  const response = await api.post<MockSpeakingSubmission>(ADMIN_ENDPOINTS.mockExamSpeakingSubmissionAiEvaluate(id));
  return response.data;
}

export async function reviewSpeakingSubmission(
  id: string,
  data: MockSpeakingSubmissionTeacherUpdate,
): Promise<MockSpeakingSubmission> {
  const response = await api.put<MockSpeakingSubmission>(ADMIN_ENDPOINTS.mockExamSpeakingSubmissionReview(id), data);
  return response.data;
}

// ============================================================
// Analytics
// ============================================================

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await api.get<DashboardSummary>(ADMIN_ENDPOINTS.mockExamDashboardSummary);
  return response.data;
}

export async function getModelTestAnalytics(modelTestId: string): Promise<ModelTestAnalytics> {
  const response = await api.get<ModelTestAnalytics>(ADMIN_ENDPOINTS.mockExamModelTestAnalytics(modelTestId));
  return response.data;
}

export async function getProviderAnalytics(providerId: string): Promise<CertificationProviderAnalytics> {
  const response = await api.get<CertificationProviderAnalytics>(
    ADMIN_ENDPOINTS.mockExamProviderAnalytics(providerId),
  );
  return response.data;
}
