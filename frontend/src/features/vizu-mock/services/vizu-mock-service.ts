import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

import type {
  VizuMockAttempt,
  VizuMockHoerenResult,
  VizuMockHoerenTask,
  VizuMockLesenResult,
  VizuMockTask,
} from "../types/vizu-mock.types";

const ROOT = "/api/v1/vizu-mock";
const BASE = `${ROOT}/attempts`;

export async function createVizuMockAttempt(): Promise<VizuMockAttempt> {
  const response = await api.post<VizuMockAttempt>(BASE);
  return response.data;
}

export async function listVizuMockAttempts(): Promise<VizuMockAttempt[]> {
  const response = await api.get<VizuMockAttempt[]>(BASE);
  return ensureArray<VizuMockAttempt>(response.data);
}

export async function getVizuMockAttempt(attemptId: string): Promise<VizuMockAttempt> {
  const response = await api.get<VizuMockAttempt>(`${BASE}/${attemptId}`);
  return response.data;
}

export async function completeVizuMockAttempt(attemptId: string): Promise<VizuMockAttempt> {
  const response = await api.post<VizuMockAttempt>(`${BASE}/${attemptId}/complete`);
  return response.data;
}

// ---- Lesen ----

export async function getVizuMockLesenTasks(): Promise<VizuMockTask[]> {
  const response = await api.get<VizuMockTask[]>(`${ROOT}/lesen/tasks`);
  return ensureArray<VizuMockTask>(response.data);
}

export interface VizuMockAnswerSubmit {
  question_id: string;
  /** null = left unanswered (e.g. the timer expired first). */
  option_id: string | null;
}

export async function submitVizuMockLesen(
  attemptId: string,
  answers: VizuMockAnswerSubmit[],
): Promise<VizuMockLesenResult> {
  const response = await api.post<VizuMockLesenResult>(`${BASE}/${attemptId}/lesen/submit`, { answers });
  return response.data;
}

export async function getVizuMockLesenResult(attemptId: string): Promise<VizuMockLesenResult> {
  const response = await api.get<VizuMockLesenResult>(`${BASE}/${attemptId}/lesen/result`);
  return response.data;
}

// ---- Hören ----

export async function getVizuMockHoerenTasks(): Promise<VizuMockHoerenTask[]> {
  const response = await api.get<VizuMockHoerenTask[]>(`${ROOT}/hoeren/tasks`);
  return ensureArray<VizuMockHoerenTask>(response.data);
}

export async function submitVizuMockHoeren(
  attemptId: string,
  answers: VizuMockAnswerSubmit[],
): Promise<VizuMockHoerenResult> {
  const response = await api.post<VizuMockHoerenResult>(`${BASE}/${attemptId}/hoeren/submit`, { answers });
  return response.data;
}

export async function getVizuMockHoerenResult(attemptId: string): Promise<VizuMockHoerenResult> {
  const response = await api.get<VizuMockHoerenResult>(`${BASE}/${attemptId}/hoeren/result`);
  return response.data;
}
