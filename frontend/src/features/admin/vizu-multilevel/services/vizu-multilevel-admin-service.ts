import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

import { ADMIN_ENDPOINTS } from "../../constants/endpoints";
import type {
  VizuMultilevelActivityStats,
  VizuMultilevelAdminAttemptItem,
  VizuMultilevelAdminAttemptsPage,
  VizuMultilevelContentTask,
  VizuMultilevelContentTaskPayload,
  VizuMultilevelQuestionPayload,
  VizuMultilevelSpeakingTaskAdmin,
  VizuMultilevelSpeakingTaskPayload,
  VizuMultilevelStatistics,
  VizuMultilevelWritingTaskCreatePayload,
  VizuMultilevelAnalytics,
  VizuMultilevelAudio,
  VizuMultilevelAudioCreatePayload,
  VizuMultilevelAudioUpdatePayload,
  VizuMultilevelLevelAnalytics,
  VizuMultilevelOverviewStats,
  VizuMultilevelWritingTaskAdmin,
  VizuMultilevelWritingTaskAdminPayload,
} from "../types/vizu-multilevel-admin.types";

export async function getVizuMultilevelOverview(): Promise<VizuMultilevelOverviewStats> {
  const response = await api.get<VizuMultilevelOverviewStats>(ADMIN_ENDPOINTS.vizuMultilevelOverview);
  return response.data;
}

export async function getVizuMultilevelActivity(days: 7 | 30): Promise<VizuMultilevelActivityStats> {
  const response = await api.get<VizuMultilevelActivityStats>(ADMIN_ENDPOINTS.vizuMultilevelActivity, { params: { days } });
  return response.data;
}

export async function getVizuMultilevelLevelAnalytics(): Promise<VizuMultilevelLevelAnalytics> {
  const response = await api.get<VizuMultilevelLevelAnalytics>(ADMIN_ENDPOINTS.vizuMultilevelLevelAnalytics);
  return response.data;
}

export async function getVizuMultilevelAnalytics(): Promise<VizuMultilevelAnalytics> {
  const response = await api.get<VizuMultilevelAnalytics>(ADMIN_ENDPOINTS.vizuMultilevelAnalytics);
  return response.data;
}

export interface VizuMultilevelAttemptsQuery {
  page?: number;
  page_size?: number;
  search?: string;
  level?: string;
  status?: string;
}

export async function listVizuMultilevelAttempts(query: VizuMultilevelAttemptsQuery): Promise<VizuMultilevelAdminAttemptsPage> {
  const response = await api.get<VizuMultilevelAdminAttemptsPage>(ADMIN_ENDPOINTS.vizuMultilevelAttempts, { params: query });
  return response.data;
}

export async function getVizuMultilevelAttemptDetail(attemptId: string): Promise<VizuMultilevelAdminAttemptItem> {
  const response = await api.get<VizuMultilevelAdminAttemptItem>(ADMIN_ENDPOINTS.vizuMultilevelAttemptDetail(attemptId));
  return response.data;
}

export async function getVizuMultilevelLesenContent(): Promise<VizuMultilevelContentTask[]> {
  const response = await api.get<VizuMultilevelContentTask[]>(ADMIN_ENDPOINTS.vizuMultilevelLesenContent);
  return ensureArray<VizuMultilevelContentTask>(response.data);
}

export interface VizuMultilevelLesenJsonImportResult {
  status: "imported" | "unchanged";
  aufgaben: number;
  questions: number;
}

// Replaces ONLY the Lesen content from lesen.json — the bundled dataset when
// no file is given. Transactional; an identical dataset is a no-op.
export async function importVizuMultilevelLesenJson(file?: File | null): Promise<VizuMultilevelLesenJsonImportResult> {
  const formData = new FormData();
  if (file) formData.append("file", file);
  const response = await api.post<VizuMultilevelLesenJsonImportResult>(
    ADMIN_ENDPOINTS.vizuMultilevelLesenContentImportJson,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export interface VizuMultilevelLesenCsvImportResult {
  tasks_created: number;
  tasks_updated: number;
  questions_created: number;
  questions_updated: number;
  total_questions: number;
}

// Imports VIZU-Multilevel's own Lesen Aufgabe/question/option content — see
// backend/app/services/vizu_multilevel/lesen_csv_import_service.py.
export async function importVizuMultilevelLesenCsv(file: File): Promise<VizuMultilevelLesenCsvImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<VizuMultilevelLesenCsvImportResult>(
    ADMIN_ENDPOINTS.vizuMultilevelLesenContentImportCsv,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export async function getVizuMultilevelHoerenContent(): Promise<VizuMultilevelContentTask[]> {
  const response = await api.get<VizuMultilevelContentTask[]>(ADMIN_ENDPOINTS.vizuMultilevelHoerenContent);
  return ensureArray<VizuMultilevelContentTask>(response.data);
}

export interface VizuMultilevelHoerenCsvImportResult {
  tasks_created: number;
  tasks_updated: number;
  questions_created: number;
  questions_updated: number;
  total_questions: number;
}

// Imports VIZU-Multilevel's own Hören Aufgabe/question/option content — see
// backend/app/services/vizu_multilevel/hoeren_csv_import_service.py. Entirely
// independent of the regular course lesson's Quiz/CSV import (if any).
export async function importVizuMultilevelHoerenCsv(file: File): Promise<VizuMultilevelHoerenCsvImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<VizuMultilevelHoerenCsvImportResult>(
    ADMIN_ENDPOINTS.vizuMultilevelHoerenContentImportCsv,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export async function listVizuMultilevelSchreibenTasks(): Promise<VizuMultilevelWritingTaskAdmin[]> {
  const response = await api.get<VizuMultilevelWritingTaskAdmin[]>(ADMIN_ENDPOINTS.vizuMultilevelSchreibenContent);
  return ensureArray<VizuMultilevelWritingTaskAdmin>(response.data);
}

export async function updateVizuMultilevelSchreibenTask(
  taskId: string,
  data: VizuMultilevelWritingTaskAdminPayload,
): Promise<VizuMultilevelWritingTaskAdmin> {
  const response = await api.put<VizuMultilevelWritingTaskAdmin>(ADMIN_ENDPOINTS.vizuMultilevelSchreibenContentDetail(taskId), data);
  return response.data;
}

export async function listVizuMultilevelAudio(): Promise<VizuMultilevelAudio[]> {
  const response = await api.get<VizuMultilevelAudio[]>(ADMIN_ENDPOINTS.vizuMultilevelAudio);
  return ensureArray<VizuMultilevelAudio>(response.data);
}

export async function createVizuMultilevelAudio(data: VizuMultilevelAudioCreatePayload): Promise<VizuMultilevelAudio> {
  const response = await api.post<VizuMultilevelAudio>(ADMIN_ENDPOINTS.vizuMultilevelAudio, data);
  return response.data;
}

export async function updateVizuMultilevelAudio(id: string, data: VizuMultilevelAudioUpdatePayload): Promise<VizuMultilevelAudio> {
  const response = await api.put<VizuMultilevelAudio>(ADMIN_ENDPOINTS.vizuMultilevelAudioDetail(id), data);
  return response.data;
}

export async function deleteVizuMultilevelAudio(id: string): Promise<void> {
  await api.delete(ADMIN_ENDPOINTS.vizuMultilevelAudioDetail(id));
}

// ---- Lesen / Hören content authoring ----

export async function createVizuMultilevelContentTask(
  skill: "lesen" | "hoeren",
  data: VizuMultilevelContentTaskPayload,
): Promise<VizuMultilevelContentTask> {
  const response = await api.post<VizuMultilevelContentTask>(ADMIN_ENDPOINTS.vizuMultilevelContentTasks(skill), data);
  return response.data;
}

export async function updateVizuMultilevelContentTask(
  taskId: string,
  data: VizuMultilevelContentTaskPayload,
): Promise<VizuMultilevelContentTask> {
  const response = await api.put<VizuMultilevelContentTask>(ADMIN_ENDPOINTS.vizuMultilevelContentTask(taskId), data);
  return response.data;
}

export async function deleteVizuMultilevelContentTask(taskId: string): Promise<void> {
  await api.delete(ADMIN_ENDPOINTS.vizuMultilevelContentTask(taskId));
}

export async function createVizuMultilevelContentQuestion(
  taskId: string,
  data: VizuMultilevelQuestionPayload,
): Promise<VizuMultilevelContentTask> {
  const response = await api.post<VizuMultilevelContentTask>(
    ADMIN_ENDPOINTS.vizuMultilevelContentTaskQuestions(taskId),
    data,
  );
  return response.data;
}

export async function updateVizuMultilevelContentQuestion(
  questionId: string,
  data: VizuMultilevelQuestionPayload,
): Promise<VizuMultilevelContentTask> {
  const response = await api.put<VizuMultilevelContentTask>(ADMIN_ENDPOINTS.vizuMultilevelContentQuestion(questionId), data);
  return response.data;
}

export async function deleteVizuMultilevelContentQuestion(questionId: string): Promise<VizuMultilevelContentTask> {
  const response = await api.delete<VizuMultilevelContentTask>(ADMIN_ENDPOINTS.vizuMultilevelContentQuestion(questionId));
  return response.data;
}

// ---- Schreiben create / delete (update lives above) ----

export async function createVizuMultilevelSchreibenTask(
  data: VizuMultilevelWritingTaskCreatePayload,
): Promise<VizuMultilevelWritingTaskAdmin> {
  const response = await api.post<VizuMultilevelWritingTaskAdmin>(ADMIN_ENDPOINTS.vizuMultilevelSchreibenContent, data);
  return response.data;
}

export async function deleteVizuMultilevelSchreibenTask(taskId: string): Promise<void> {
  await api.delete(ADMIN_ENDPOINTS.vizuMultilevelSchreibenContentDetail(taskId));
}

// ---- Sprechen ----

export async function listVizuMultilevelSprechenTasks(): Promise<VizuMultilevelSpeakingTaskAdmin[]> {
  const response = await api.get<VizuMultilevelSpeakingTaskAdmin[]>(ADMIN_ENDPOINTS.vizuMultilevelSprechenContent);
  return ensureArray<VizuMultilevelSpeakingTaskAdmin>(response.data);
}

export async function createVizuMultilevelSprechenTask(
  data: VizuMultilevelSpeakingTaskPayload,
): Promise<VizuMultilevelSpeakingTaskAdmin> {
  const response = await api.post<VizuMultilevelSpeakingTaskAdmin>(ADMIN_ENDPOINTS.vizuMultilevelSprechenContent, data);
  return response.data;
}

export async function updateVizuMultilevelSprechenTask(
  taskId: string,
  data: VizuMultilevelSpeakingTaskPayload,
): Promise<VizuMultilevelSpeakingTaskAdmin> {
  const response = await api.put<VizuMultilevelSpeakingTaskAdmin>(
    ADMIN_ENDPOINTS.vizuMultilevelSprechenContentDetail(taskId),
    data,
  );
  return response.data;
}

export async function deleteVizuMultilevelSprechenTask(taskId: string): Promise<void> {
  await api.delete(ADMIN_ENDPOINTS.vizuMultilevelSprechenContentDetail(taskId));
}

// ---- Statistics ----

export async function getVizuMultilevelStatistics(): Promise<VizuMultilevelStatistics> {
  const response = await api.get<VizuMultilevelStatistics>(ADMIN_ENDPOINTS.vizuMultilevelStatistics);
  return response.data;
}
