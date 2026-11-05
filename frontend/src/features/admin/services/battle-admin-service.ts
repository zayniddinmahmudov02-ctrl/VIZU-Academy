import { api } from "@/services/api";
import type { Attribution, Stage, Theme } from "@/features/battle/services/battle-service";

const BASE = "/api/v1/admin/battle";

export type WordStatus = "draft" | "published" | "disabled";
export type ImageStatus = "draft" | "verified" | "published" | "rejected";

export interface AdminImage {
  id: string;
  status: ImageStatus;
  source: "wikimedia" | "upload";
  source_url: string | null;
  file_title: string | null;
  author: string | null;
  license: string | null;
  license_url: string | null;
  width: number;
  height: number;
  size_bytes: number;
  review_note: string | null;
  verified_at: string | null;
}

export interface AdminWord {
  id: string;
  level: string;
  article: string | null;
  lemma: string;
  display: string;
  translation: string;
  category: string;
  status: WordStatus;
  image: AdminImage | null;
}

export interface BattleOverview {
  levels: Record<string, { words: number; published: number; playable: number; without_image: number }>;
  images: Record<ImageStatus, number>;
  stages: Record<Stage, { pool: number; ready: boolean }>;
  matches_7d: { mode: string; status: string; count: number }[];
  players: number;
  categories: Record<string, { de: string; uz: string }>;
  min_pool: number;
}

export interface CommonsItem {
  title: string;
  page_url: string;
  thumb_url: string;
  license: string;
  license_url: string | null;
  author: string | null;
  width: number;
  height: number;
}

export type ThemeDraft = Partial<Pick<Theme, "city" | "title" | "subtitle" | "desktop_image" | "mobile_image" | "accent" | "overlay" | "is_active">> & { attribution?: Attribution };
export type AdminTheme = Theme & { draft: (ThemeDraft & Record<string, unknown>) | null; missing?: boolean };

export const getBattleOverview = async () => (await api.get<BattleOverview>(`${BASE}/overview`)).data;

export const getBattleWords = async (params: { level?: string; status?: string; category?: string; q?: string; page?: number }) => {
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ""));
  return (await api.get<{ items: AdminWord[]; total: number; page: number; page_size: number }>(`${BASE}/words`, { params: clean })).data;
};

export const addBattleWord = async (dictionary_id: string, category: string) => (await api.post<AdminWord>(`${BASE}/words`, { dictionary_id, category })).data;

export const patchBattleWord = async (id: string, data: { category?: string; status?: WordStatus }) => (await api.patch<AdminWord>(`${BASE}/words/${id}`, data)).data;

export async function uploadBattleImage(wordId: string, file: File, meta: { author: string; license: string; source_url?: string }) {
  const form = new FormData();
  form.append("file", file);
  form.append("author", meta.author);
  form.append("license", meta.license);
  if (meta.source_url) form.append("source_url", meta.source_url);
  return (await api.post<AdminWord>(`${BASE}/words/${wordId}/image`, form, { headers: { "Content-Type": "multipart/form-data" } })).data;
}

export const searchCommons = async (q: string) => (await api.get<{ items: CommonsItem[] }>(`${BASE}/commons/search`, { params: { q } })).data.items;

export const importCommons = async (wordId: string, title: string) => (await api.post<AdminWord>(`${BASE}/words/${wordId}/commons`, { title })).data;

export const setImageStatus = async (id: string, status: ImageStatus, note?: string) =>
  (await api.post<AdminImage>(`${BASE}/images/${id}/status`, { status, ...(note ? { note } : {}) })).data;

/** The private picture as an object URL (the admin token travels in the header, not the URL). */
export async function fetchImageBlobUrl(id: string) {
  const blob = (await api.get<Blob>(`${BASE}/images/${id}/file`, { responseType: "blob" })).data;
  return URL.createObjectURL(blob);
}

export const getAdminThemes = async () => (await api.get<{ items: AdminTheme[] }>(`${BASE}/themes`)).data.items;
export const saveThemeDraft = async (stage: Stage, draft: ThemeDraft) => (await api.put<AdminTheme>(`${BASE}/themes/${encodeURIComponent(stage)}/draft`, draft)).data;
export const publishTheme = async (stage: Stage) => (await api.post<AdminTheme>(`${BASE}/themes/${encodeURIComponent(stage)}/publish`)).data;
export const discardTheme = async (stage: Stage) => (await api.post<AdminTheme>(`${BASE}/themes/${encodeURIComponent(stage)}/discard`)).data;

export async function uploadThemeAsset(kind: "desktop" | "mobile", file: File) {
  const form = new FormData();
  form.append("kind", kind);
  form.append("file", file);
  return (await api.post<{ ref: string; width: number; height: number; size_bytes: number }>(`${BASE}/themes/assets`, form, { headers: { "Content-Type": "multipart/form-data" } })).data;
}
