import { api } from "@/src/services/api";

const BASE = "/api/v1/admin/loesung";

export type LoesungKind = "lesen" | "hoeren";
export type KeyStatus = "complete" | "missing" | "needs_review";
export type AudioState = "ok" | "none" | "file_missing" | "external" | null;
export type StatusFilter = "" | "complete" | "missing" | "needs_review" | "missing_audio" | "ready" | "published" | "draft";

export interface LoesungItem {
  kind: LoesungKind;
  id: string;
  number: number;
  title: string;
  level: string;
  lesson_id: string;
  lesson_number: number;
  lesson_title: string;
  questions: number;
  with_key: number;
  verified: number;
  flagged: number;
  /** answer fields: one per gap of a Lückentext / item of a Zuordnung, one per other question */
  answer_fields: number;
  answer_fields_keyed: number;
  key_status: KeyStatus;
  audio: AudioState;
  is_published: boolean;
  ready_to_publish: boolean;
  problems: number;
  import_note: string | null;
  updated_at: string;
}

export interface LoesungStats {
  lesen_total: number;
  hoeren_total: number;
  complete: number;
  missing: number;
  needs_review: number;
  missing_audio: number;
  ready: number;
  published: number;
}

export interface LoesungOverview {
  stats: LoesungStats;
  items: LoesungItem[];
  lessons: { id: string; level: string; number: number; title: string }[];
}

export interface KeyOption {
  /** null = a new option (created on save) */
  id: string | null;
  text: string;
  is_correct: boolean;
}

export interface KeyQuestion {
  id: string;
  number: number;
  question: string;
  question_type: "MULTIPLE_CHOICE" | "TRUE_FALSE" | "MATCHING" | "GAP_FILL" | "SHORT_ANSWER";
  points: number;
  explanation: string | null;
  config: Record<string, unknown> | null;
  options: KeyOption[];
  has_key: boolean;
  key_problem: string | null;
  verified: boolean;
  needs_review: boolean;
  verification_outdated: boolean;
  note: string | null;
  reviewed_at: string | null;
  answer_fields: number;
  answer_fields_keyed: number;
}

export interface TaskRef {
  kind: LoesungKind;
  id: string;
  title: string;
  level: string;
  lesson_number: number;
}

export interface LoesungDetail extends Omit<LoesungItem, "questions"> {
  instruction: string | null;
  content: string | null;
  transcript: string | null;
  audio_name: string | null;
  audio_duration: number | null;
  import: { note: string | null; book_page: string | number | null; source: string | null; key_pending: boolean; file: string } | null;
  questions: KeyQuestion[];
  validation: { ready: boolean; problems: { code: string; question?: number; message: string }[] };
  previous: TaskRef | null;
  next: TaskRef | null;
  next_incomplete: TaskRef | null;
}

export interface OverviewFilters {
  level?: string;
  lesson_id?: string;
  section?: string;
  status?: string;
  publication?: string;
  q?: string;
}

export async function getLoesungOverview(filters: OverviewFilters): Promise<LoesungOverview> {
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  return (await api.get<LoesungOverview>(`${BASE}/overview`, { params })).data;
}

export async function getLoesungTask(kind: LoesungKind, id: string): Promise<LoesungDetail> {
  return (await api.get<LoesungDetail>(`${BASE}/${kind}/${id}`)).data;
}

export interface SaveKeyInput {
  question?: string;
  options?: KeyOption[];
  config?: Record<string, unknown> | null;
  explanation?: string | null;
  review?: "verified" | "needs_review" | "unverified";
  note?: string | null;
}

export async function saveLoesungQuestion(kind: LoesungKind, taskId: string, questionId: string, input: SaveKeyInput): Promise<LoesungDetail> {
  return (await api.put<LoesungDetail>(`${BASE}/${kind}/${taskId}/questions/${questionId}`, input)).data;
}

export async function publishLoesungTask(kind: LoesungKind, taskId: string): Promise<LoesungDetail> {
  return (await api.post<LoesungDetail>(`${BASE}/${kind}/${taskId}/publish`)).data;
}

export async function unpublishLoesungTask(kind: LoesungKind, taskId: string): Promise<LoesungDetail> {
  return (await api.post<LoesungDetail>(`${BASE}/${kind}/${taskId}/unpublish`)).data;
}

export function taskHref(kind: LoesungKind, id: string): string {
  return `/admin/lms/loesung/${kind}/${id}`;
}
