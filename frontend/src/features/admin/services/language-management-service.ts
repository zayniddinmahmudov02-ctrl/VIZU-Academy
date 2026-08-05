import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import { createCrudApi } from "../lib/crud-api";
import type {
  Language,
  LanguageCreate,
  LanguageLearnersResponse,
  LanguageSettings,
  LanguageSettingsUpdate,
  LanguageStatistics,
  LanguageUpdate,
} from "../types/language.types";

// Deliberately separate from features/admin/services/languages-service.ts
// (used by the Courses/"Levels" admin page, out of scope for this module —
// left untouched) even though both ultimately call the same backend
// /api/v1/languages/* endpoints. This module needs the full Enterprise
// Language Management surface (statistics, learners, settings); the Levels
// page only ever needed a plain id/name dropdown.
const LANGUAGES_BASE = "/api/v1/languages/";

export const languageManagementApi = createCrudApi<Language, LanguageCreate, LanguageUpdate>(LANGUAGES_BASE);

export async function getLanguage(id: string): Promise<Language> {
  const response = await api.get<Language>(`${LANGUAGES_BASE}${id}`);
  return response.data;
}

export async function getLanguageStatistics(id: string): Promise<LanguageStatistics> {
  const response = await api.get<LanguageStatistics>(`${LANGUAGES_BASE}${id}/statistics`);
  return response.data;
}

export async function getLanguageLearners(
  id: string,
  params: { search?: string; page?: number; page_size?: number },
): Promise<LanguageLearnersResponse> {
  const response = await api.get<LanguageLearnersResponse>(`${LANGUAGES_BASE}${id}/learners`, { params });
  return {
    ...response.data,
    items: ensureArray(response.data?.items),
  };
}

export async function getLanguageSettings(id: string): Promise<LanguageSettings> {
  const response = await api.get<LanguageSettings>(`${LANGUAGES_BASE}${id}/settings`);
  return response.data;
}

export async function updateLanguageSettings(
  id: string,
  data: LanguageSettingsUpdate,
): Promise<LanguageSettings> {
  const response = await api.put<LanguageSettings>(`${LANGUAGES_BASE}${id}/settings`, data);
  return response.data;
}

export async function uploadFlagSvg(file: File, code: string): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("code", code);

  const response = await api.post<{ filename: string }>("/api/admin/flags", formData, {
    baseURL: "",
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data.filename;
}
