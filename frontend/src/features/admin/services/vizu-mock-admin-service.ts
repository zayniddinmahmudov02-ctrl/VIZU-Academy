import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  VizuMockActivityStats,
  VizuMockAdminAttemptItem,
  VizuMockAdminAttemptsPage,
  VizuMockAdminHoerenTask,
  VizuMockAdminTask,
  VizuMockAnalytics,
  VizuMockAudio,
  VizuMockAudioCreatePayload,
  VizuMockAudioUpdatePayload,
  VizuMockLevelAnalytics,
  VizuMockOverviewStats,
  VizuMockWritingTaskAdmin,
  VizuMockWritingTaskAdminPayload,
} from "../types/vizu-mock-admin.types";

export async function getVizuMockOverview(): Promise<VizuMockOverviewStats> {
  const response = await api.get<VizuMockOverviewStats>(ADMIN_ENDPOINTS.vizuMockOverview);
  return response.data;
}

export async function getVizuMockActivity(days: 7 | 30): Promise<VizuMockActivityStats> {
  const response = await api.get<VizuMockActivityStats>(ADMIN_ENDPOINTS.vizuMockActivity, { params: { days } });
  return response.data;
}

export async function getVizuMockLevelAnalytics(): Promise<VizuMockLevelAnalytics> {
  const response = await api.get<VizuMockLevelAnalytics>(ADMIN_ENDPOINTS.vizuMockLevelAnalytics);
  return response.data;
}

export async function getVizuMockAnalytics(): Promise<VizuMockAnalytics> {
  const response = await api.get<VizuMockAnalytics>(ADMIN_ENDPOINTS.vizuMockAnalytics);
  return response.data;
}

export interface VizuMockAttemptsQuery {
  page?: number;
  page_size?: number;
  search?: string;
  level?: string;
  status?: string;
}

export async function listVizuMockAttempts(query: VizuMockAttemptsQuery): Promise<VizuMockAdminAttemptsPage> {
  const response = await api.get<VizuMockAdminAttemptsPage>(ADMIN_ENDPOINTS.vizuMockAttempts, { params: query });
  return response.data;
}

export async function getVizuMockAttemptDetail(attemptId: string): Promise<VizuMockAdminAttemptItem> {
  const response = await api.get<VizuMockAdminAttemptItem>(ADMIN_ENDPOINTS.vizuMockAttemptDetail(attemptId));
  return response.data;
}

export async function getVizuMockLesenContent(): Promise<VizuMockAdminTask[]> {
  const response = await api.get<VizuMockAdminTask[]>(ADMIN_ENDPOINTS.vizuMockLesenContent);
  return ensureArray<VizuMockAdminTask>(response.data);
}

export interface VizuMockLesenCsvImportResult {
  tasks_created: number;
  tasks_updated: number;
  questions_created: number;
  questions_updated: number;
  total_questions: number;
}

// Imports VIZU-Mock's own Lesen Aufgabe/question/option content — see
// backend/app/services/vizu_mock/lesen_csv_import_service.py.
export async function importVizuMockLesenCsv(file: File): Promise<VizuMockLesenCsvImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<VizuMockLesenCsvImportResult>(
    ADMIN_ENDPOINTS.vizuMockLesenContentImportCsv,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export async function getVizuMockHoerenContent(): Promise<VizuMockAdminHoerenTask[]> {
  const response = await api.get<VizuMockAdminHoerenTask[]>(ADMIN_ENDPOINTS.vizuMockHoerenContent);
  return ensureArray<VizuMockAdminHoerenTask>(response.data);
}

export interface VizuMockHoerenCsvImportResult {
  tasks_created: number;
  tasks_updated: number;
  questions_created: number;
  questions_updated: number;
  total_questions: number;
}

// Imports VIZU-Mock's own Hören Aufgabe/question/option content — see
// backend/app/services/vizu_mock/hoeren_csv_import_service.py. Entirely
// independent of the regular course lesson's Quiz/CSV import (if any).
export async function importVizuMockHoerenCsv(file: File): Promise<VizuMockHoerenCsvImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<VizuMockHoerenCsvImportResult>(
    ADMIN_ENDPOINTS.vizuMockHoerenContentImportCsv,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export async function listVizuMockSchreibenTasks(): Promise<VizuMockWritingTaskAdmin[]> {
  const response = await api.get<VizuMockWritingTaskAdmin[]>(ADMIN_ENDPOINTS.vizuMockSchreibenContent);
  return ensureArray<VizuMockWritingTaskAdmin>(response.data);
}

export async function updateVizuMockSchreibenTask(
  taskId: string,
  data: VizuMockWritingTaskAdminPayload,
): Promise<VizuMockWritingTaskAdmin> {
  const response = await api.put<VizuMockWritingTaskAdmin>(ADMIN_ENDPOINTS.vizuMockSchreibenContentDetail(taskId), data);
  return response.data;
}

export async function listVizuMockAudio(): Promise<VizuMockAudio[]> {
  const response = await api.get<VizuMockAudio[]>(ADMIN_ENDPOINTS.vizuMockAudio);
  return ensureArray<VizuMockAudio>(response.data);
}

export async function createVizuMockAudio(data: VizuMockAudioCreatePayload): Promise<VizuMockAudio> {
  const response = await api.post<VizuMockAudio>(ADMIN_ENDPOINTS.vizuMockAudio, data);
  return response.data;
}

export async function updateVizuMockAudio(id: string, data: VizuMockAudioUpdatePayload): Promise<VizuMockAudio> {
  const response = await api.put<VizuMockAudio>(ADMIN_ENDPOINTS.vizuMockAudioDetail(id), data);
  return response.data;
}

export async function deleteVizuMockAudio(id: string): Promise<void> {
  await api.delete(ADMIN_ENDPOINTS.vizuMockAudioDetail(id));
}
