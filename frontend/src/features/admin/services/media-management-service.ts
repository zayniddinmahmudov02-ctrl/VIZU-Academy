import { api } from "@/src/services/api";
import type { AudioSlot } from "@/features/admin/services/lesson-skills-admin-service";

const BASE = "/api/v1/admin/media-management";

export interface MediaTreeLesson { id: string; number: number; title: string }
export interface MediaTreeModule { id: string; number: number; title: string; lessons: MediaTreeLesson[] }
export interface MediaTreeLevel { level: string; course_id: string; modules: MediaTreeModule[] }

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

export interface A2ListeningSlotTask {
  id: string;
  title: string;
  order_index: number;
  is_published: boolean;
  audio_original_name: string | null;
  audio_format: string | null;
  audio_duration_seconds: number | null;
  file_status: MediaFileStatus;
  question_count: number;
  key_missing: number;
}

export interface A2ListeningMaterial {
  key: string;
  slot_number: number;
  source_name: string;
  expected_format: string;
  format_matches: boolean | null;
  listening: A2ListeningSlotTask | null;
  available_task_ids: string[];
}

export interface A2ListeningLesson {
  lesson_number: number;
  lesson_id: string | null;
  lesson_title: string | null;
  lesson_exists: boolean;
  expected_materials: A2ListeningMaterial[];
  other_tasks: A2ListeningSlotTask[];
}

export interface A2ListeningOverview {
  expected_lesson_count: number;
  actual_lesson_count: number;
  lesson_count_matches: boolean;
  expected_audio_count: number;
  mapped_audio_count: number;
  uploaded_audio_count: number;
  format_mismatch_count: number;
  audio_count_matches: boolean;
  lessons: A2ListeningLesson[];
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

export async function getA2ListeningOverview(): Promise<A2ListeningOverview> {
  return (await api.get<A2ListeningOverview>(`${BASE}/a2-audio`)).data;
}

export async function createA2ListeningSlotTask(lessonNumber: number, materialKey: string): Promise<A2ListeningSlotTask> {
  return (await api.post<A2ListeningSlotTask>(`${BASE}/a2-audio/lessons/${lessonNumber}/materials`, { material_key: materialKey })).data;
}

export async function assignA2ListeningSlotTask(materialKey: string, listeningId: string): Promise<A2ListeningSlotTask> {
  return (await api.put<A2ListeningSlotTask>(`${BASE}/a2-audio/materials/${materialKey}/assign`, { listening_id: listeningId })).data;
}
