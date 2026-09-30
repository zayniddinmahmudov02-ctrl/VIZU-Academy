import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

import type { VizuMockAttempt } from "../types/vizu-mock.types";

const BASE = "/api/v1/vizu-mock/attempts";

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
