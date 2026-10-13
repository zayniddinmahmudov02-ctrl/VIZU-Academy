import { api } from "@/src/services/api";

import type { CompetencyKind, ResourceType } from "@/features/lms/types";

/** VIZU LMS course editor — admin API (backend: app/api/lms/admin_router.py,
 * app/api/videos/router.py). Reads: any admin-panel role; changes: SUPER_ADMIN,
 * ADMIN, CONTENT_MANAGER (enforced on the server). */

const BASE = "/api/v1/admin/lms";
// the shared client defaults to JSON — multipart must be set per upload
const MULTIPART = { "Content-Type": "multipart/form-data" };

export interface AdminLevelSummary {
  level: string;
  course_id: string | null;
  module_id: string | null;
  title: string | null;
  sequential_unlock: boolean;
  lessons_target: number;
  lessons_existing: number;
  lessons_published: number;
  numbers_missing: number[];
  numbers_outside_range: number[];
}

export interface AdminLessonCard {
  id: string;
  number: number;
  title: string;
  description: string | null;
  duration: number;
  is_published: boolean;
  access_override: "OPEN" | "LOCKED" | null;
  competencies_published: number;
  videos: number;
  videos_published: number;
  resources: number;
}

export interface AdminLevelLessons extends AdminLevelSummary {
  lessons: AdminLessonCard[];
}

export type Count = { total: number; published: number };

export interface AdminCompetency {
  kind: CompetencyKind;
  position: number;
  body: string | null;
  is_published: boolean;
  content: {
    videos: number;
    resources: number;
    frage?: Count;
    words?: number;
    rules?: number;
    readings?: number;
    listenings?: number;
    exercises?: Count;
    tasks?: Count;
  };
}

export interface AdminLmsVideo {
  id: string;
  title: string;
  competency: CompetencyKind;
  order_index: number;
  duration_seconds: number;
  is_published: boolean;
  file_status: "ok" | "missing" | "no_file";
  has_subtitles: boolean;
  subtitle_status: "ok" | "missing" | null;
}

export interface AdminResource {
  id: string;
  lesson_id: string;
  competency: CompetencyKind | null;
  resource_type: ResourceType;
  title: string;
  description: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  duration_seconds: number | null;
  order_index: number;
  external_url: string | null;
  is_published: boolean;
  original_filename: string | null;
  file_status: "ok" | "missing" | null;
  preview_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminLmsLesson {
  lesson: {
    id: string;
    number: number;
    title: string;
    description: string | null;
    duration: number;
    is_published: boolean;
    access_override: "OPEN" | "LOCKED" | null;
    level: string | null;
    lessons_in_level: number | null;
  };
  competencies: AdminCompetency[];
  videos: AdminLmsVideo[];
  resources: AdminResource[];
}

export interface LessonPatch {
  title?: string;
  description?: string | null;
  duration?: number;
  is_published?: boolean;
  access_override?: "OPEN" | "LOCKED" | null;
  number?: number;
}

export interface ProgressPage {
  page: number;
  page_size: number;
  total: number;
  items: {
    user_id: string;
    name: string | null;
    lesson_completed: boolean;
    completed_at: string | null;
    last_activity_at: string | null;
    competencies: Partial<Record<CompetencyKind, { status: string; score: number | null; completed_at: string | null }>>;
  }[];
}

export interface StorageHealth {
  totals: { checked: number; missing: number };
  lessons: {
    level: string;
    lesson_id: string;
    number: number;
    title: string;
    problems: { kind: string; id: string; title: string; status: string; published: boolean }[];
  }[];
}

export const getAdminLevels = async () => (await api.get<{ total_lessons_target: number; levels: AdminLevelSummary[] }>(`${BASE}/levels`)).data;
export const getAdminLevelLessons = async (level: string) => (await api.get<AdminLevelLessons>(`${BASE}/levels/${level}/lessons`)).data;
export const updateLevel = async (level: string, sequential_unlock: boolean) =>
  (await api.patch<AdminLevelSummary>(`${BASE}/levels/${level}`, { sequential_unlock })).data;
export const ensureStructure = async (level: string) =>
  (await api.post<{ created: { course: boolean; module: boolean; lessons: number[]; competencies: number }; summary: AdminLevelSummary }>(`${BASE}/levels/${level}/ensure-structure`)).data;
export const reorderLessons = async (level: string, lessonIds: string[]) =>
  (await api.post<{ lessons: AdminLessonCard[] }>(`${BASE}/levels/${level}/reorder`, { lesson_ids: lessonIds })).data;

export const getAdminLmsLesson = async (lessonId: string) => (await api.get<AdminLmsLesson>(`${BASE}/lessons/${lessonId}`)).data;
export const updateLmsLesson = async (lessonId: string, data: LessonPatch) => (await api.patch<AdminLmsLesson>(`${BASE}/lessons/${lessonId}`, data)).data;
export const updateCompetency = async (lessonId: string, kind: CompetencyKind, data: { body?: string | null; is_published?: boolean }) =>
  (await api.patch<AdminLmsLesson>(`${BASE}/lessons/${lessonId}/competencies/${kind}`, data)).data;

export async function uploadResource(
  lessonId: string,
  data: { file: File; resource_type: Exclude<ResourceType, "LINK">; title: string; competency: CompetencyKind | null; description?: string; duration_seconds?: number | null },
  onProgress?: (percent: number) => void,
) {
  const form = new FormData();
  form.append("file", data.file);
  form.append("resource_type", data.resource_type);
  form.append("title", data.title);
  if (data.competency) form.append("competency", data.competency);
  if (data.description) form.append("description", data.description);
  if (data.duration_seconds) form.append("duration_seconds", String(data.duration_seconds));
  return (
    await api.post<AdminResource>(`${BASE}/lessons/${lessonId}/resources`, form, {
      timeout: 0,
      headers: MULTIPART,
      onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded / e.total) * 100)),
    })
  ).data;
}

export const createLink = async (lessonId: string, data: { url: string; title: string; competency: CompetencyKind | null; description?: string }) =>
  (await api.post<AdminResource>(`${BASE}/lessons/${lessonId}/links`, data)).data;
export const updateResource = async (id: string, data: Partial<{ title: string; description: string | null; competency: CompetencyKind | null; order_index: number; is_published: boolean; url: string }>) =>
  (await api.patch<AdminResource>(`${BASE}/resources/${id}`, data)).data;
export async function replaceResourceFile(id: string, file: File, onProgress?: (percent: number) => void) {
  const form = new FormData();
  form.append("file", file);
  return (
    await api.put<AdminResource>(`${BASE}/resources/${id}/file`, form, {
      timeout: 0,
      headers: MULTIPART,
      onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded / e.total) * 100)),
    })
  ).data;
}
export const deleteResource = async (id: string) => {
  await api.delete(`${BASE}/resources/${id}`);
};
/** Admin preview: the file through the authenticated admin endpoint, as a
 * blob URL (the caller revokes it). */
export async function resourcePreviewUrl(id: string): Promise<string> {
  const res = await api.get<Blob>(`${BASE}/resources/${id}/file`, { responseType: "blob" });
  return URL.createObjectURL(res.data);
}

export const getLessonProgress = async (lessonId: string, page: number, pageSize = 20) =>
  (await api.get<ProgressPage>(`${BASE}/lessons/${lessonId}/progress`, { params: { page, page_size: pageSize } })).data;
export const getStorageHealth = async (level?: string) =>
  (await api.get<StorageHealth>(`${BASE}/storage-health`, { params: level ? { level } : {} })).data;

// videos (existing endpoints)
export const setVideoCompetency = async (videoId: string, competency: CompetencyKind | null) => {
  await api.put(`/api/v1/videos/${videoId}`, { competency: competency === "EINFUEHRUNG" ? null : competency });
};
export const setVideoPublished = async (videoId: string, published: boolean) => {
  await api.patch(`/api/v1/videos/${videoId}/${published ? "publish" : "unpublish"}`);
};
export async function uploadSubtitles(videoId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  await api.post(`/api/v1/videos/${videoId}/subtitles`, form, { headers: MULTIPART });
}
export const deleteSubtitles = async (videoId: string) => {
  await api.delete(`/api/v1/videos/${videoId}/subtitles`);
};

const ERROR_TEXT: Record<string, string> = {
  "Content editor access required": "Keine Berechtigung: Inhalte dürfen nur Super-Admin, Admin und Content-Manager ändern.",
  LESSON_NUMBER_TAKEN: "Diese Lektionsnummer ist in diesem Niveau schon vergeben.",
  LESSON_NUMBER_REQUIRED: "Bitte eine Lektionsnummer angeben.",
  UNKNOWN_COMPETENCY: "Unbekannte Kompetenz.",
  UNKNOWN_RESOURCE_TYPE: "Unbekannter Dateityp.",
  LINK_HAS_NO_FILE: "Ein Link hat keine Datei.",
  REORDER_MUST_LIST_EVERY_LESSON_ONCE: "Die Reihenfolge muss jede Lektion genau einmal enthalten.",
  RESOURCE_FILE_MISSING: "Die Datei fehlt auf dem Server.",
  LANGUAGE_DE_MISSING: "Die Sprache „de“ ist nicht angelegt.",
  LEVEL_NOT_SET_UP: "Dieses Niveau ist noch nicht angelegt — zuerst „Struktur anlegen“.",
};

/** A backend error as text an editor understands (upload type / size errors
 * come from the server with the allowed formats). */
export function lmsAdminError(err: unknown, fallback = "Aktion fehlgeschlagen."): string {
  const res = (err as { response?: { status?: number; data?: { message?: unknown; detail?: unknown } } })?.response;
  if (!res) return "Keine Verbindung zum Server — bitte erneut versuchen.";
  const raw = res.data?.message ?? res.data?.detail;
  if (typeof raw === "string" && raw) {
    if (ERROR_TEXT[raw]) return ERROR_TEXT[raw];
    if (raw.startsWith("UNSUPPORTED_FILE")) return `Dateityp nicht erlaubt (${raw.split(":").slice(1).join(":").trim()}).`;
    if (raw.startsWith("FILE_TOO_LARGE")) return `Datei zu groß (${raw.split(":").slice(1).join(":").trim()}).`;
    if (raw.startsWith("INVALID_URL")) return "Nur https://-Links sind erlaubt.";
    if (raw.startsWith("LESSON_NUMBER_OUT_OF_RANGE")) return `Lektionsnummer außerhalb des Niveaus (${raw.split(":").slice(1).join(":").trim()}).`;
    if (raw.startsWith("UNSUPPORTED_SUBTITLES")) return "Nur WebVTT-Untertitel (.vtt) sind erlaubt.";
    if (raw.startsWith("SUBTITLES_TOO_LARGE")) return "Untertiteldatei zu groß (max. 2 MB).";
    return raw;
  }
  if (res.status === 403) return ERROR_TEXT["Content editor access required"];
  if (res.status === 413) return "Datei zu groß.";
  if (res.status && res.status >= 500) return "Serverfehler — bitte erneut versuchen.";
  return fallback;
}
