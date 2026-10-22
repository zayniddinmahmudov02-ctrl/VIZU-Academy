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

export interface A2AudioTask {
  id: string;
  title: string;
  order_index: number;
  is_published: boolean;
  audio_original_name: string | null;
  audio_format: string | null;
  audio_size_bytes: number | null;
  audio_duration_seconds: number | null;
  file_status: MediaFileStatus;
  format_error: boolean;
  question_count: number;
  key_missing: number;
  audio_slots: AudioSlot[];
  material_key: string | null;
  unverified_source_hint: string | null;
  archived_versions: number;
}

export interface A2AudioLesson {
  lesson_id: string;
  lesson_number: number;
  lesson_title: string;
  tasks: A2AudioTask[];
  task_count: number;
  uploaded_count: number;
  missing_count: number;
}

export interface A2AudioOverview {
  /** false: the A2 book is not available, so nothing is confirmed against it */
  book_confirmed: boolean;
  lesson_count: number;
  /** null while the book is unconfirmed */
  expected_audio_slots: number | null;
  task_count: number;
  uploaded_audio_count: number;
  missing_audio_count: number;
  format_error_count: number;
  lessons: A2AudioLesson[];
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

export async function getA2AudioOverview(): Promise<A2AudioOverview> {
  return (await api.get<A2AudioOverview>(`${BASE}/a2-audio`)).data;
}
