import { api } from "@/src/services/api";
import type { AdminQuestion, AudioSlot } from "@/features/admin/services/lesson-skills-admin-service";

const BASE = "/api/v1/admin/media-management";

export interface MediaTreeLesson { id: string; number: number; title: string }
export interface MediaTreeModule { id: string; number: number; title: string; lessons: MediaTreeLesson[] }
export interface MediaTreeLevel { level: string; course_id: string; modules: MediaTreeModule[] }

export interface A2AudioTask {
  id: string;
  material_key: string | null;
  title: string;
  order_index: number;
  is_published: boolean;
  audio_original_name: string | null;
  audio_content_type: string | null;
  audio_format: string | null;
  audio_duration_seconds: number | null;
  file_status: MediaFileStatus;
  questions: AdminQuestion[];
  question_count: number;
  key_missing: number;
  extra_audio_tracks: AudioSlot[];
  archive: { id: string; original_name: string | null; content_type: string | null; size_bytes: number | null; duration_seconds: number | null; archived_at: string }[];
}
export interface A2AudioMaterialSlot {
  key: string;
  slot_number: number;
  source_name: string;
  expected_format: string;
  format_matches: boolean | null;
  listening: A2AudioTask | null;
  suggested_task_ids: string[];
  available_task_ids: string[];
}
export interface A2AudioLesson {
  lesson_number: number;
  lesson_id: string | null;
  lesson_title: string | null;
  lesson_exists: boolean;
  expected_materials: A2AudioMaterialSlot[];
  other_tasks: A2AudioTask[];
}
export interface A2AudioOverview {
  expected_lesson_count: number;
  actual_lesson_count: number;
  expected_audio_count: number;
  mapped_audio_count: number;
  uploaded_audio_count: number;
  format_mismatch_count: number;
  lesson_count_matches: boolean;
  audio_count_matches: boolean;
  lessons: A2AudioLesson[];
}

export type MediaKind = "VIDEO" | "AUDIO";
export type MediaFileStatus = "ok" | "missing" | "external" | "none";

export interface MediaItem {
  kind: MediaKind;
  id: string;
  level: string;
  module_number: number;
  lesson_id: string;
  lesson_number: number;
  lesson_title: string;
  title: string;
  file_name: string | null;
  size_bytes: number | null;
  duration_seconds: number | null;
  file_status: MediaFileStatus;
  /** video: competency it is shown in; audio: the Hören task */
  task: string;
  is_published: boolean;
  /** audio only: every question has an answer key */
  has_key: boolean | null;
  questions?: number;
  /** audio only: the main audio + labelled extra tracks (e.g. "Audio von Alisa" / "Audio von Alex") */
  audio_slots?: AudioSlot[];
  created_at: string;
  updated_at: string;
}

export async function getMediaTree(): Promise<MediaTreeLevel[]> {
  return (await api.get<MediaTreeLevel[]>(`${BASE}/tree`)).data;
}

export async function getMediaItems(): Promise<MediaItem[]> {
  const data = (await api.get<MediaItem[]>(`${BASE}/items`)).data;
  return Array.isArray(data) ? data : [];
}

/** Short-lived signed URL (relative) for the admin video player — drafts too. */
export async function getVideoPreviewUrl(videoId: string): Promise<string> {
  return (await api.get<{ url: string }>(`${BASE}/videos/${videoId}/preview`)).data.url;
}

const A2_BASE = `${BASE}/a2-audio`;

export async function getA2AudioOverview(): Promise<A2AudioOverview> {
  return (await api.get<A2AudioOverview>(A2_BASE)).data;
}

export async function createA2AudioTask(lessonNumber: number, materialKey: string): Promise<A2AudioTask> {
  return (await api.post<A2AudioTask>(`${A2_BASE}/lessons/${lessonNumber}/materials`, { material_key: materialKey })).data;
}

export async function assignA2AudioTask(materialKey: string, listeningId: string): Promise<A2AudioTask> {
  return (await api.put<A2AudioTask>(`${A2_BASE}/materials/${materialKey}/assign`, { listening_id: listeningId })).data;
}

export async function updateA2AudioTask(
  materialKey: string,
  changes: { title?: string; order_index?: number; is_published?: boolean },
): Promise<A2AudioTask> {
  return (await api.patch<A2AudioTask>(`${A2_BASE}/materials/${materialKey}`, changes)).data;
}

export async function uploadA2Audio(materialKey: string, file: File, durationSeconds: number | null): Promise<A2AudioTask> {
  const form = new FormData();
  form.append("file", file);
  if (durationSeconds !== null) form.append("duration_seconds", String(durationSeconds));
  return (await api.post<A2AudioTask>(`${A2_BASE}/materials/${materialKey}/audio`, form)).data;
}

export async function getA2AudioBlobUrl(materialKey: string, archiveId?: string): Promise<string> {
  const path = archiveId
    ? `${A2_BASE}/materials/${materialKey}/archive/${archiveId}/preview`
    : `${A2_BASE}/materials/${materialKey}/preview`;
  const response = await api.get<Blob>(path, { responseType: "blob" });
  return URL.createObjectURL(response.data);
}
