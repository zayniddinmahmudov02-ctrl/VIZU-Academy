import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

import type {
  PublicKompetenzDetail,
  PublicLevel,
  PublicModelTest,
  PublicModelTestDetail,
  PublicProvider,
} from "../types/vorbereitung.types";

const BASE = "/api/v1/mock-exam/public";

export async function getPublicProviders(): Promise<PublicProvider[]> {
  const response = await api.get<PublicProvider[]>(`${BASE}/providers`);
  return ensureArray<PublicProvider>(response.data);
}

export async function getPublicLevels(providerId: string): Promise<PublicLevel[]> {
  const response = await api.get<PublicLevel[]>(`${BASE}/levels`, { params: { provider_id: providerId } });
  return ensureArray<PublicLevel>(response.data);
}

export async function getPublicModelTests(levelId: string): Promise<PublicModelTest[]> {
  const response = await api.get<PublicModelTest[]>(`${BASE}/model-tests`, { params: { level_id: levelId } });
  return ensureArray<PublicModelTest>(response.data);
}

export async function getPublicModelTest(modelTestId: string): Promise<PublicModelTestDetail> {
  const response = await api.get<PublicModelTestDetail>(`${BASE}/model-tests/${modelTestId}`);
  return response.data;
}

export async function getPublicKompetenz(kompetenzId: string): Promise<PublicKompetenzDetail> {
  const response = await api.get<PublicKompetenzDetail>(`${BASE}/kompetenzen/${kompetenzId}`);
  return response.data;
}
