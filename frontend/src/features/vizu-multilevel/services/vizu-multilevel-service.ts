import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

import type {
  VizuMultilevelAnswerSubmit,
  VizuMultilevelAttempt,
  VizuMultilevelAttemptResult,
  VizuMultilevelAttemptState,
  VizuMultilevelCertificate,
  VizuMultilevelCompleteResponse,
  VizuMultilevelHoerenResult,
  VizuMultilevelHoerenTask,
  VizuMultilevelLesenResult,
  VizuMultilevelSectionState,
  VizuMultilevelSkill,
  VizuMultilevelSpeakingSubmission,
  VizuMultilevelSpeakingTask,
  VizuMultilevelTask,
  VizuMultilevelWritingSubmission,
  VizuMultilevelWritingTask,
} from "../types/vizu-multilevel.types";

const ROOT = "/api/v1/vizu-multilevel";
const BASE = `${ROOT}/attempts`;

// ---- Attempts / flow ----

export async function createVizuMultilevelAttempt(): Promise<VizuMultilevelAttempt> {
  const response = await api.post<VizuMultilevelAttempt>(BASE);
  return response.data;
}

export async function listVizuMultilevelAttempts(): Promise<VizuMultilevelAttempt[]> {
  const response = await api.get<VizuMultilevelAttempt[]>(BASE);
  return ensureArray<VizuMultilevelAttempt>(response.data);
}

export async function getVizuMultilevelAttempt(attemptId: string): Promise<VizuMultilevelAttempt> {
  const response = await api.get<VizuMultilevelAttempt>(`${BASE}/${attemptId}`);
  return response.data;
}

export async function getVizuMultilevelAttemptState(attemptId: string): Promise<VizuMultilevelAttemptState> {
  const response = await api.get<VizuMultilevelAttemptState>(`${BASE}/${attemptId}/state`);
  return response.data;
}

/** Idempotent: the server stamps the start of a competency's 20-minute
 * window once; a reload returns the same deadline, never a fresh timer. */
export async function startVizuMultilevelSection(
  attemptId: string,
  skill: VizuMultilevelSkill,
): Promise<VizuMultilevelSectionState> {
  const response = await api.post<VizuMultilevelSectionState>(`${BASE}/${attemptId}/${skill}/start`);
  return response.data;
}

export async function getVizuMultilevelResult(attemptId: string): Promise<VizuMultilevelAttemptResult> {
  const response = await api.get<VizuMultilevelAttemptResult>(`${BASE}/${attemptId}/result`);
  return response.data;
}

export async function completeVizuMultilevelAttempt(attemptId: string): Promise<VizuMultilevelCompleteResponse> {
  const response = await api.post<VizuMultilevelCompleteResponse>(`${BASE}/${attemptId}/complete`);
  return response.data;
}

export async function getVizuMultilevelCertificate(attemptId: string): Promise<VizuMultilevelCertificate> {
  const response = await api.get<VizuMultilevelCertificate>(`${BASE}/${attemptId}/certificate`);
  return response.data;
}

// ---- Lesen ----

export async function getVizuMultilevelLesenTasks(): Promise<VizuMultilevelTask[]> {
  const response = await api.get<VizuMultilevelTask[]>(`${ROOT}/lesen/tasks`);
  return ensureArray<VizuMultilevelTask>(response.data);
}

export async function submitVizuMultilevelLesen(
  attemptId: string,
  answers: VizuMultilevelAnswerSubmit[],
): Promise<VizuMultilevelLesenResult> {
  const response = await api.post<VizuMultilevelLesenResult>(`${BASE}/${attemptId}/lesen/submit`, { answers });
  return response.data;
}

// ---- Hören ----

export async function getVizuMultilevelHoerenTasks(): Promise<VizuMultilevelHoerenTask[]> {
  const response = await api.get<VizuMultilevelHoerenTask[]>(`${ROOT}/hoeren/tasks`);
  return ensureArray<VizuMultilevelHoerenTask>(response.data);
}

export async function submitVizuMultilevelHoeren(
  attemptId: string,
  answers: VizuMultilevelAnswerSubmit[],
): Promise<VizuMultilevelHoerenResult> {
  const response = await api.post<VizuMultilevelHoerenResult>(`${BASE}/${attemptId}/hoeren/submit`, { answers });
  return response.data;
}

/** Autosaved answers (question_id -> option_id), restored after a refresh. */
export async function getVizuMultilevelHoerenDraft(attemptId: string): Promise<Record<string, string>> {
  const response = await api.get<{ answers: Record<string, string> }>(`${BASE}/${attemptId}/hoeren/answers`);
  return response.data.answers ?? {};
}

export async function saveVizuMultilevelHoerenDraft(attemptId: string, answers: VizuMultilevelAnswerSubmit[]): Promise<void> {
  await api.put(`${BASE}/${attemptId}/hoeren/answers`, { answers });
}

/** Streams one Aufgabe's audio through the authenticated endpoint and
 * returns a short-lived blob URL for the <audio> element. */
export async function getVizuMultilevelHoerenAudioBlobUrl(attemptId: string, aufgabeNumber: number): Promise<string> {
  const response = await api.get(`${BASE}/${attemptId}/hoeren/aufgabe/${aufgabeNumber}/audio`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

// ---- Schreiben ----

export async function getVizuMultilevelSchreibenTasks(): Promise<VizuMultilevelWritingTask[]> {
  const response = await api.get<VizuMultilevelWritingTask[]>(`${ROOT}/schreiben/tasks`);
  return ensureArray<VizuMultilevelWritingTask>(response.data);
}

export async function getVizuMultilevelSchreibenSubmissions(attemptId: string): Promise<VizuMultilevelWritingSubmission[]> {
  const response = await api.get<VizuMultilevelWritingSubmission[]>(`${BASE}/${attemptId}/schreiben/submissions`);
  return ensureArray<VizuMultilevelWritingSubmission>(response.data);
}

export async function saveVizuMultilevelSchreibenDraft(
  attemptId: string,
  taskId: string,
  content: string,
): Promise<VizuMultilevelWritingSubmission> {
  const response = await api.put<VizuMultilevelWritingSubmission>(`${BASE}/${attemptId}/schreiben/save`, {
    task_id: taskId,
    content,
  });
  return response.data;
}

export async function submitVizuMultilevelSchreiben(attemptId: string): Promise<void> {
  await api.post(`${BASE}/${attemptId}/schreiben/submit`);
}

// ---- Sprechen ----

export async function getVizuMultilevelSprechenTasks(): Promise<VizuMultilevelSpeakingTask[]> {
  const response = await api.get<VizuMultilevelSpeakingTask[]>(`${ROOT}/sprechen/tasks`);
  return ensureArray<VizuMultilevelSpeakingTask>(response.data);
}

export async function getVizuMultilevelSprechenSubmissions(attemptId: string): Promise<VizuMultilevelSpeakingSubmission[]> {
  const response = await api.get<VizuMultilevelSpeakingSubmission[]>(`${BASE}/${attemptId}/sprechen/submissions`);
  return ensureArray<VizuMultilevelSpeakingSubmission>(response.data);
}

export async function uploadVizuMultilevelSprechenRecording(
  attemptId: string,
  taskId: string,
  blob: Blob,
  durationSeconds: number,
): Promise<VizuMultilevelSpeakingSubmission> {
  const formData = new FormData();
  formData.append("task_id", taskId);
  formData.append("duration_seconds", String(Math.round(durationSeconds)));
  formData.append("file", blob, "recording.webm");
  const response = await api.post<VizuMultilevelSpeakingSubmission>(`${BASE}/${attemptId}/sprechen/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function submitVizuMultilevelSprechen(attemptId: string): Promise<void> {
  await api.post(`${BASE}/${attemptId}/sprechen/submit`);
}
