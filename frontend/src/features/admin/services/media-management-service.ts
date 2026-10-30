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
  archived_versions: number;
}

export interface A2AudioLesson {
  lesson_id: string;
  lesson_number: number;
  lesson_title: string;
  tasks: A2AudioTask[];
  task_count: number;
  media_file_count: number;
  question_count: number;
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
  /** DB points at a file that no longer exists in storage */
  stale_record_count: number;
  /** stored files no task/track/archive of any level references (report only) */
  unreferenced_files: { file_name: string; size_bytes: number }[];
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

// ---------- A2 Audio Manager (library, manifest, links, readiness) ----------

export type A2AudioKind = "HOEREN" | "TEXT" | "UNTERRICHT" | "OTHER";
export type A2Verification = "pending" | "verified" | "problem";

export interface A2Asset {
  id: string;
  unterricht: number | null;
  audio_kind: A2AudioKind | null;
  part: number | null;
  title: string;
  original_filename: string;
  /** what the file name parser read */
  parsed: { recognized: boolean; unterricht: number | null; audio_kind: A2AudioKind | null; part: number | null } | null;
  audio_format: string;
  size_bytes: number;
  sha256: string;
  duration_seconds: number | null;
  sort_order: number;
  file_status: "ok" | "missing";
  verification: A2Verification;
  verification_note: string | null;
  verified_at: string | null;
  linked: { listening_id: string; title: string; lesson_number: number | null; is_published: boolean; in_sync: boolean } | null;
  link_mismatch: boolean;
  /** what the file name suggests — only applied when the admin confirms it */
  suggestion: { listening_id: string; title: string; lesson_number: number; reason: string } | null;
  created_at: string;
}

export interface A2Target {
  listening_id: string;
  lesson_number: number;
  lesson_title: string;
  title: string;
  order_index: number;
  content_id: string | null;
  is_published: boolean;
  has_audio: boolean;
  asset_id: string | null;
}

export interface A2ManifestTask { listening_id: string; lesson_number: number; title: string; has_audio: boolean; asset_id: string | null }

export interface A2Manifest {
  counts: {
    files: number; size_bytes: number; by_format: Record<string, number>; by_kind: Record<string, number>;
    verified: number; problem: number; pending: number; linked: number; unlinked: number; missing_file: number; no_unterricht: number;
    tasks: number; tasks_with_audio: number; tasks_without_audio: number;
  };
  missing_audio: A2ManifestTask[];
}

export interface A2ReadinessCheck { key: string; group: string; ok: boolean; label: string; detail: string | null; items: string[]; manual?: boolean }

export interface A2Readiness {
  status: "READY" | "NEEDS_CONTENT" | "NEEDS_CONFIGURATION" | "NEEDS_TESTING";
  sales_enabled: boolean;
  checks: A2ReadinessCheck[];
  content_gaps: string[];
}

export interface A2AssetFields { unterricht?: number | null; audio_kind?: A2AudioKind | null; part?: number | null; title?: string; sort_order?: number }

export async function getA2Assets(): Promise<A2Asset[]> {
  return (await api.get<A2Asset[]>(`${BASE}/a2-audio/assets`)).data ?? [];
}

export async function getA2Targets(): Promise<A2Target[]> {
  return (await api.get<A2Target[]>(`${BASE}/a2-audio/targets`)).data ?? [];
}

export async function getA2Manifest(): Promise<A2Manifest> {
  return (await api.get<A2Manifest>(`${BASE}/a2-audio/manifest`)).data;
}

export async function getA2Readiness(): Promise<A2Readiness> {
  return (await api.get<A2Readiness>(`${BASE}/a2-readiness`)).data;
}

export async function confirmA2ReadinessCheck(key: string, done: boolean, note?: string): Promise<A2Readiness> {
  return (await api.post<A2Readiness>(`${BASE}/a2-readiness/checks`, { key, done, note: note || null })).data;
}

/** One file per request; the batch upload calls this file after file. */
export async function uploadA2Asset(file: File, durationSeconds: number | null, onProgress?: (percent: number) => void): Promise<A2Asset> {
  const form = new FormData();
  form.append("file", file);
  if (durationSeconds) form.append("duration_seconds", String(Math.round(durationSeconds)));
  return (await api.post<A2Asset>(`${BASE}/a2-audio/assets`, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: onProgress ? (e) => e.total && onProgress(Math.round((e.loaded / e.total) * 100)) : undefined,
  })).data;
}

export async function updateA2Asset(id: string, fields: A2AssetFields): Promise<A2Asset> {
  return (await api.patch<A2Asset>(`${BASE}/a2-audio/assets/${id}`, fields)).data;
}

export async function verifyA2Asset(id: string, state: A2Verification, note?: string): Promise<A2Asset> {
  return (await api.post<A2Asset>(`${BASE}/a2-audio/assets/${id}/verify`, { state, note: note || null })).data;
}

export async function linkA2Asset(id: string, listeningId: string): Promise<A2Asset> {
  return (await api.post<A2Asset>(`${BASE}/a2-audio/assets/${id}/link`, { listening_id: listeningId })).data;
}

export async function unlinkA2Asset(id: string): Promise<A2Asset> {
  return (await api.post<A2Asset>(`${BASE}/a2-audio/assets/${id}/unlink`)).data;
}

export async function deleteA2Asset(id: string, deleteFile: boolean): Promise<{ file_deleted: boolean }> {
  return (await api.delete(`${BASE}/a2-audio/assets/${id}`, { params: { delete_file: deleteFile } })).data;
}

export async function getA2AssetBlobUrl(id: string): Promise<string> {
  const response = await api.get(`${BASE}/a2-audio/assets/${id}/audio`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

// ---------- A2 audio processing (lessons 1-13): transcript, match, keys, publish ----------

export type A2PipelineStatus =
  | "UPLOADED" | "TRANSCRIBING" | "TRANSCRIBED" | "MATCHED" | "ANSWER_KEY_VERIFIED" | "PUBLISHED" | "NEEDS_REVIEW" | "FAILED";

export interface A2TranscriptSegment { start: number; end: number; text: string }

export interface A2ProcessingFile {
  slot: string;
  label: string | null;
  name: string | null;
  size_bytes: number | null;
  duration_seconds: number | null;
  on_disk: boolean;
  transcript: {
    sha256: string;
    status: "TRANSCRIBING" | "TRANSCRIBED" | "NEEDS_REVIEW" | "FAILED";
    model: string | null;
    text: string | null;
    segments: A2TranscriptSegment[] | null;
    quality: { agreement?: number | null; second_model?: string; low_confidence_words?: number; words?: number; uncertain?: { at: number; heard: string }[] } | null;
    review_note: string | null;
    duration_seconds: number | null;
  } | null;
}

export interface A2ProcessingQuestion {
  number: number;
  question: string;
  type: string;
  options: { text: string; is_correct: boolean }[];
  config: { text?: string; gaps?: Record<string, { accepted?: string[]; options?: string[] }>; pairs?: Record<string, string>; items?: { id: string; text: string }[]; targets?: { id: string; text: string }[] } | null;
  has_key: boolean;
  verified: boolean;
  needs_review: boolean;
  note: string | null;
}

export interface A2ProcessingTask {
  listening_id: string;
  title: string;
  content_id: string | null;
  task_key: string | null;
  is_published: boolean;
  status: A2PipelineStatus;
  problems: string[];
  match: { status: "MATCHED" | "NEEDS_REVIEW" | "MISMATCH"; note?: string } | null;
  keys: { total: number; verified: number; needs_review: number; missing: number };
  questions: A2ProcessingQuestion[];
  student_transcript: boolean;
  library_verification: A2Verification | null;
  files: A2ProcessingFile[];
}

export interface A2Processing {
  summary: {
    tasks: number; published: number; percent_published: number; by_status: Record<A2PipelineStatus, number>;
    audio_files: number; transcribed: number; unique_contents: number; matched: number; keys_verified: number;
  };
  lessons: { number: number; title: string | null; is_published: boolean; tasks: A2ProcessingTask[]; task_count: number; published_tasks: number }[];
}

export async function getA2Processing(): Promise<A2Processing> {
  return (await api.get<A2Processing>(`${BASE}/a2-audio/processing`)).data;
}

// ---------- A2 → 4. Unterricht → Hören: Text 1 / 2 / 3 ----------

export type A2TextSlotNumber = 1 | 2 | 3;

export interface A2TextSlot {
  slot: A2TextSlotNumber;
  label: string;
  task_key: string;
  exists: boolean;
  listening_id?: string;
  title?: string;
  is_published?: boolean;
  question_count?: number;
  audio?: {
    status: "none" | "ok" | "missing";
    file_name: string | null;
    size_bytes: number | null;
    duration_seconds: number | null;
    format: string | null;
    source: "library" | "task" | null;
  };
  asset?: { id: string; verification: A2Verification; verification_note: string | null; verified_at: string | null; sha256: string; uploaded_at: string } | null;
  verified?: boolean;
  can_activate?: boolean;
  activate_blocker?: string | null;
  reused?: boolean;
}

export interface A2Lesson4Hoeren {
  lesson_id: string;
  lesson_number: number;
  lesson_title: string;
  set_up: boolean;
  slots: A2TextSlot[];
  legacy_tasks: { listening_id: string; title: string; is_published: boolean }[];
}

const L4 = `${BASE}/a2/lesson-4/hoeren`;

export async function getA2Lesson4Hoeren(): Promise<A2Lesson4Hoeren> {
  return (await api.get<A2Lesson4Hoeren>(L4)).data;
}

export async function setupA2Lesson4Hoeren(): Promise<A2Lesson4Hoeren> {
  return (await api.post<A2Lesson4Hoeren>(`${L4}/setup`)).data;
}

export async function uploadA2TextAudio(slot: A2TextSlotNumber, file: File, durationSeconds: number | null, onProgress?: (percent: number) => void): Promise<A2TextSlot> {
  const form = new FormData();
  form.append("file", file);
  if (durationSeconds) form.append("duration_seconds", String(Math.round(durationSeconds)));
  return (await api.post<A2TextSlot>(`${L4}/${slot}/audio`, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: onProgress ? (e) => e.total && onProgress(Math.round((e.loaded / e.total) * 100)) : undefined,
  })).data;
}

export async function deleteA2TextAudio(slot: A2TextSlotNumber): Promise<A2TextSlot & { file_deleted: boolean }> {
  return (await api.delete(`${L4}/${slot}/audio`)).data;
}

export async function verifyA2TextAudio(slot: A2TextSlotNumber, state: A2Verification, note?: string): Promise<A2TextSlot> {
  return (await api.post<A2TextSlot>(`${L4}/${slot}/verify`, { state, note: note || null })).data;
}

export async function setA2TextActive(slot: A2TextSlotNumber, active: boolean): Promise<A2TextSlot> {
  return (await api.post<A2TextSlot>(`${L4}/${slot}/active`, { active })).data;
}

export async function getA2TextAudioBlobUrl(slot: A2TextSlotNumber): Promise<string> {
  const response = await api.get(`${L4}/${slot}/audio`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}
