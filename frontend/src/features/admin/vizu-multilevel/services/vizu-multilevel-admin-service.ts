import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

import { savePdfBlob } from "@/features/vizu-multilevel/services/vizu-multilevel-service";

import { ADMIN_ENDPOINTS } from "../../constants/endpoints";
import type {
  VizuMultilevelActivityStats,
  VizuMultilevelAdminAttemptItem,
  VizuMultilevelAdminAttemptsPage,
  VizuMultilevelContentTask,
  VizuMultilevelContentTaskPayload,
  VizuMultilevelQuestionPayload,
  VizuMultilevelCertificateStatus,
  VizuMultilevelSpeakingAttemptDetail,
  VizuMultilevelSpeakingTaskAdmin,
  VizuMultilevelSpeakingTaskPayload,
  VizuMultilevelStatistics,
  VizuMultilevelWritingTaskCreatePayload,
  VizuMultilevelAnalytics,
  VizuMultilevelHoerenAudioSlot,
  VizuMultilevelHoerenDiagnostics,
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

// ---- Hören audio (protected, one file per Aufgabe 1-5) ----

export async function listVizuMultilevelHoerenAudio(): Promise<VizuMultilevelHoerenAudioSlot[]> {
  const response = await api.get<VizuMultilevelHoerenAudioSlot[]>(ADMIN_ENDPOINTS.vizuMultilevelHoerenAudio);
  return ensureArray<VizuMultilevelHoerenAudioSlot>(response.data);
}

function audioForm(file: File, durationSeconds: number | null, aufgabeNumber?: number): FormData {
  const formData = new FormData();
  if (aufgabeNumber !== undefined) formData.append("aufgabe_number", String(aufgabeNumber));
  if (durationSeconds !== null) formData.append("duration_seconds", String(Math.round(durationSeconds)));
  formData.append("file", file);
  return formData;
}

const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };

/** The admin explicitly picks the Aufgabe; uploading again replaces its audio. */
export async function uploadVizuMultilevelHoerenAudio(
  aufgabeNumber: number,
  file: File,
  durationSeconds: number | null,
): Promise<VizuMultilevelHoerenAudioSlot> {
  const response = await api.post<VizuMultilevelHoerenAudioSlot>(
    ADMIN_ENDPOINTS.vizuMultilevelHoerenAudio,
    audioForm(file, durationSeconds, aufgabeNumber),
    MULTIPART,
  );
  return response.data;
}

export async function replaceVizuMultilevelHoerenAudio(
  audioId: string,
  file: File,
  durationSeconds: number | null,
): Promise<VizuMultilevelHoerenAudioSlot> {
  const response = await api.put<VizuMultilevelHoerenAudioSlot>(
    ADMIN_ENDPOINTS.vizuMultilevelHoerenAudioDetail(audioId),
    audioForm(file, durationSeconds),
    MULTIPART,
  );
  return response.data;
}

export async function deleteVizuMultilevelHoerenAudio(audioId: string): Promise<void> {
  await api.delete(ADMIN_ENDPOINTS.vizuMultilevelHoerenAudioDetail(audioId));
}

/** Admin preview: authenticated fetch -> blob URL (no public URL exists). */
export async function getVizuMultilevelHoerenAudioPreviewUrl(audioId: string): Promise<string> {
  const response = await api.get(`${ADMIN_ENDPOINTS.vizuMultilevelHoerenAudioDetail(audioId)}/file`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

/** Real database counts: Aufgaben / Tests / Optionen / Audio. */
export async function getVizuMultilevelHoerenDiagnostics(): Promise<VizuMultilevelHoerenDiagnostics> {
  const response = await api.get<VizuMultilevelHoerenDiagnostics>(ADMIN_ENDPOINTS.vizuMultilevelHoerenDiagnostics);
  return response.data;
}

export interface VizuMultilevelHoerenJsonImportResult {
  status: "imported" | "unchanged";
  aufgaben: number;
  questions: number;
}

/** Loads the bundled hoeren.json (replaces only Hören content; uploaded audio is kept). */
export async function importVizuMultilevelHoerenJson(): Promise<VizuMultilevelHoerenJsonImportResult> {
  const response = await api.post<VizuMultilevelHoerenJsonImportResult>(ADMIN_ENDPOINTS.vizuMultilevelHoerenContentImportJson);
  return response.data;
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

/** null = this attempt has not submitted Sprechen yet (404). */
export async function getVizuMultilevelAttemptSprechen(attemptId: string): Promise<VizuMultilevelSpeakingAttemptDetail | null> {
  try {
    const response = await api.get<VizuMultilevelSpeakingAttemptDetail>(ADMIN_ENDPOINTS.vizuMultilevelAttemptSprechen(attemptId));
    return response.data;
  } catch (error) {
    if ((error as { response?: { status?: number } }).response?.status === 404) return null;
    throw error;
  }
}

/** The private recording as a blob (the endpoint needs the admin's token, so
 * it cannot be an <audio src> URL directly). */
export async function getVizuMultilevelAttemptSprechenAudio(attemptId: string, submissionId: string): Promise<Blob> {
  const response = await api.get<Blob>(ADMIN_ENDPOINTS.vizuMultilevelAttemptSprechenAudio(attemptId, submissionId), {
    responseType: "blob",
  });
  return response.data;
}

// ---- Statistics ----

export async function getVizuMultilevelStatistics(): Promise<VizuMultilevelStatistics> {
  const response = await api.get<VizuMultilevelStatistics>(ADMIN_ENDPOINTS.vizuMultilevelStatistics);
  return response.data;
}

// ---- Certificate ----

export async function getVizuMultilevelAttemptCertificate(attemptId: string): Promise<VizuMultilevelCertificateStatus> {
  const response = await api.get<VizuMultilevelCertificateStatus>(ADMIN_ENDPOINTS.vizuMultilevelAttemptCertificate(attemptId));
  return response.data;
}

export async function downloadVizuMultilevelAttemptCertificatePdf(attemptId: string): Promise<void> {
  const response = await api.get<Blob>(ADMIN_ENDPOINTS.vizuMultilevelAttemptCertificatePdf(attemptId), { responseType: "blob" });
  savePdfBlob(response.data, response.headers["content-disposition"] as string | undefined, "VIZU-Zertifikat.pdf");
}
