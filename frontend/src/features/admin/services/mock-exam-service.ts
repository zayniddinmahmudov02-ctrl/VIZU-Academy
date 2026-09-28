import { api } from "@/src/services/api";
import { createCrudApi, createWriteOnlyCrudApi } from "../lib/crud-api";
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
  ModelTest,
  ModelTestAnalytics,
  ModelTestCreate,
  ModelTestScore,
  ModelTestUpdate,
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
// Content (Listening audio / Writing / Speaking tasks) — 1:1 with a Teil
// ============================================================

export const mockExamListeningContentApi = createWriteOnlyCrudApi<
  ListeningContent,
  ListeningContentCreate,
  ListeningContentUpdate
>(ADMIN_ENDPOINTS.mockExamListeningContent);

export const mockExamWritingTasksApi = createWriteOnlyCrudApi<WritingTask, WritingTaskCreate, WritingTaskUpdate>(
  ADMIN_ENDPOINTS.mockExamWritingTasks,
);

export const mockExamSpeakingTasksApi = createWriteOnlyCrudApi<SpeakingTask, SpeakingTaskCreate, SpeakingTaskUpdate>(
  ADMIN_ENDPOINTS.mockExamSpeakingTasks,
);

async function getOrNull<T>(url: string): Promise<T | null> {
  const response = await api.get<T | null>(url);
  return response.data ?? null;
}

export const getListeningContentByTeil = (teilId: string) =>
  getOrNull<ListeningContent>(ADMIN_ENDPOINTS.mockExamListeningContentByTeil(teilId));
export const getWritingTaskByTeil = (teilId: string) =>
  getOrNull<WritingTask>(ADMIN_ENDPOINTS.mockExamWritingTaskByTeil(teilId));
export const getSpeakingTaskByTeil = (teilId: string) =>
  getOrNull<SpeakingTask>(ADMIN_ENDPOINTS.mockExamSpeakingTaskByTeil(teilId));

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
