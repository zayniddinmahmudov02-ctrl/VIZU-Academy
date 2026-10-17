import { api } from "@/src/services/api";

const BASE = "/api/v1/admin/hoeren-a1";

export type SlotStatus = "new" | "match" | "conflict" | "suspicious" | "invalid";

export interface HoerenSlot {
  id: string;
  question_no: number;
  question: string;
  kind: "MC" | "TF" | "GAP";
  gap_id: string | null;
  context: string;
  current: string | null;
  answer: string | null;
  hint: string | null;
  status: SlotStatus;
  note: string | null;
}

export interface HoerenTaskPlan {
  listening_id: string;
  title: string;
  problem: string | null;
  pdf_answers: string[];
  slots: HoerenSlot[];
}

export interface HoerenLessonPlan {
  lesson_number: number;
  lesson_id: string | null;
  lesson_title: string | null;
  heading: string;
  status: "ok" | "no_answers" | "no_tasks" | "not_assigned" | "lesson_missing";
  note: string | null;
  tasks: HoerenTaskPlan[];
}

export interface HoerenSummary {
  lessons: number;
  lessons_assigned: number;
  new: number;
  match: number;
  conflict: number;
  suspicious: number;
  invalid: number;
}

export interface HoerenTaskStatus {
  listening_id: string;
  lesson_id?: string;
  lesson_number: number;
  lesson_title?: string;
  title: string;
  is_published: boolean;
  audio_name?: string | null;
  audio: "ok" | "none" | "file_missing";
  questions: number;
  key_missing: number;
  ready: boolean;
  reasons: string[];
  result?: "published" | "already" | "not_ready" | "not_a1";
}

export interface HoerenApplyResult {
  written: number;
  review_skipped: number;
  publish: HoerenTaskStatus[];
  summary_after: HoerenSummary;
  lessons_after: HoerenLessonPlan[];
}

function form(file: File, accepted?: string[]) {
  const f = new FormData();
  f.append("file", file);
  if (accepted) f.append("accepted", JSON.stringify(accepted));
  return f;
}

export async function previewHoerenPdf(file: File) {
  return (await api.post<{ summary: HoerenSummary; lessons: HoerenLessonPlan[] }>(`${BASE}/answers-pdf/preview`, form(file), {
    headers: { "Content-Type": "multipart/form-data" },
  })).data;
}

export async function applyHoerenPdf(file: File, accepted: string[]) {
  return (await api.post<HoerenApplyResult>(`${BASE}/answers-pdf/apply`, form(file, accepted), {
    headers: { "Content-Type": "multipart/form-data" },
  })).data;
}

export async function getHoerenA1Status(): Promise<HoerenTaskStatus[]> {
  const data = (await api.get<HoerenTaskStatus[]>(`${BASE}/status`)).data;
  return Array.isArray(data) ? data : [];
}

export async function publishReadyHoerenA1(): Promise<HoerenTaskStatus[]> {
  return (await api.post<HoerenTaskStatus[]>(`${BASE}/publish-ready`)).data;
}
