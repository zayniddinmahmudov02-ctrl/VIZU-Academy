import { api } from "@/src/services/api";

import type { AdminQuestion, RubricCriterion } from "./lesson-skills-admin-service";

/** LMS A1-C1: course (level) structure, overall-result configuration and the
 * Claude/JSON content import (backend: app/api/lesson_skills/admin_router.py,
 * app/api/content_import/router.py). Admin-panel roles only. */

export const LMS_LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;
export type LmsLevel = (typeof LMS_LEVELS)[number];
// lesson order (lesson flow v3) — the skills of the lesson result
export const SKILL_KEYS = ["frage", "grammatik", "lesen", "hoeren", "schreiben", "sprechen", "wortschatz", "yakuniy"] as const;
export type SkillKey = (typeof SKILL_KEYS)[number];
export const SKILL_LABELS: Record<SkillKey, string> = {
  frage: "Frage des Themas",
  grammatik: "Grammatik",
  lesen: "Lesen",
  hoeren: "Hören",
  schreiben: "Schreiben",
  sprechen: "Sprechen",
  wortschatz: "Wortschatz",
  yakuniy: "Yakuniy Test",
};
// content columns of the course structure (grammatik = rules, wortschatz =
// words, uebungen = Grammatik / Wortschatz exercise sets)
export const STRUCTURE_KEYS = ["frage", "grammatik", "lesen", "hoeren", "schreiben", "sprechen", "wortschatz", "uebungen", "yakuniy"] as const;
export type StructureKey = (typeof STRUCTURE_KEYS)[number];
export const STRUCTURE_LABELS: Record<StructureKey, string> = {
  frage: "Frage",
  grammatik: "Regeln",
  lesen: "Lesen",
  hoeren: "Hören",
  schreiben: "Schreiben",
  sprechen: "Sprechen",
  wortschatz: "Wörter",
  uebungen: "Übungen",
  yakuniy: "Yakuniy",
};

export interface ResultConfig {
  weights: Record<SkillKey, number>;
  required: SkillKey[];
}

export interface SkillCount {
  total: number;
  published: number;
}

export interface CourseStructure {
  course: { id: string; level: string; title: string; is_active: boolean };
  result_config: ResultConfig;
  result_config_is_default: boolean;
  modules: {
    id: string;
    number: number;
    title: string;
    is_active: boolean;
    lessons: { id: string; number: number; title: string; skills: Partial<Record<StructureKey, SkillCount>> }[];
  }[];
}

const SKILLS_BASE = "/api/v1/admin/lesson-skills";
const IMPORT_BASE = "/api/v1/admin/content-import";

export async function getCourseStructure(courseId: string): Promise<CourseStructure> {
  const data = (await api.get<CourseStructure>(`${SKILLS_BASE}/courses/${courseId}/structure`)).data;
  return { ...data, modules: Array.isArray(data?.modules) ? data.modules : [] };
}

export async function saveResultConfig(courseId: string, config: ResultConfig) {
  return (await api.put<{ result_config: ResultConfig; result_config_is_default: boolean }>(`${SKILLS_BASE}/courses/${courseId}/result-config`, config)).data;
}

export async function resetResultConfig(courseId: string) {
  return (await api.delete<{ result_config: ResultConfig; result_config_is_default: boolean }>(`${SKILLS_BASE}/courses/${courseId}/result-config`)).data;
}

// ============================================================
// Content import
// ============================================================

export type ImportSkill = SkillKey;

export interface ImportTarget {
  level: string;
  module: number;
  lesson: number;
  course_id: string | null;
  module_id: string | null;
  lesson_id: string | null;
  lesson_title: string | null;
  create: string | null;
}

/** Normalised preview of one item (admin only — includes the answer keys). */
export interface ImportPreview {
  title: string;
  instruction: string | null;
  passages?: { title: string; text: string; image_url?: string | null }[];
  questions?: (AdminQuestion & { passage?: number })[];
  max_points?: number;
  transcript?: string | null;
  audio_hint?: string | null;
  prompt?: string;
  task_type?: string;
  audience?: string | null;
  min_words?: number | null;
  max_words?: number | null;
  time_limit?: number | null;
  support_phrases?: string[] | null;
  topic?: string | null;
  response_type?: string;
  min_duration?: number;
  max_duration?: number;
  preparation_time?: number;
  speech_goal?: string | null;
  rubric?: RubricCriterion[];
  rubric_is_default?: boolean;
  key_pending?: number;
  rules?: { title: string; html: string }[];
  exercises?: { title: string; source: "book" | "vizu"; questions: AdminQuestion[]; max_points: number }[];
  words?: { word: string; article?: string | null; plural?: string | null; translation: string; group?: string | null }[];
  auto_practice?: number;
}

export interface ImportItemReport {
  index: number;
  content_id: string | null;
  skill: ImportSkill | string | null;
  level: string | null;
  title: string | null;
  errors: string[];
  warnings: string[];
  target: ImportTarget | null;
  preview: ImportPreview | null;
  valid: boolean;
  /** re-import: why the item is skipped (already exists) */
  skip?: string | null;
  source?: "book" | "vizu" | null;
}

export interface ImportReport {
  schema_version: string;
  errors: string[];
  total: number;
  valid: number;
  invalid: number;
  skipped?: number;
  items: ImportItemReport[];
}

export interface BatchItem {
  index: number;
  content_id: string | null;
  skill: string | null;
  level: string | null;
  title: string | null;
  errors: string[];
  warnings: string[];
  status: "created" | "error" | "skipped";
  skip?: string;
  created: { kind: "reading" | "listening" | "writing" | "speaking"; id: string }[];
  published: boolean;
  publish_problem?: string;
  lesson_id?: string;
  audio_hint?: string | null;
}

export interface ImportBatch {
  id: string;
  filename: string | null;
  schema_version: string;
  levels: string[];
  total_items: number;
  created_items: number;
  failed_items: number;
  skipped_items?: number;
  published_items: number;
  created_at: string;
  published_at: string | null;
  items?: BatchItem[];
}

export interface ImportGuide {
  level: LmsLevel;
  prompt: string;
  checklist: string[];
  ranges: Record<string, [number, number]>;
  text_types: string[];
  default_rubrics: { writing: RubricCriterion[]; speaking: RubricCriterion[] };
  example: Record<string, unknown>;
}

export interface ImportStatus {
  claude_api_configured: boolean;
  model: string | null;
  note: string | null;
  levels: string[];
  schema_version: string;
}

export async function getImportStatus(): Promise<ImportStatus> {
  return (await api.get<ImportStatus>(`${IMPORT_BASE}/status`)).data;
}

export async function getImportGuide(level: LmsLevel): Promise<ImportGuide> {
  return (await api.get<ImportGuide>(`${IMPORT_BASE}/guide`, { params: { level } })).data;
}

export async function getImportSchema(): Promise<Record<string, unknown>> {
  return (await api.get<Record<string, unknown>>(`${IMPORT_BASE}/schema`)).data;
}

export async function validateImport(document: unknown, createMissing: boolean, skipExisting = false): Promise<ImportReport> {
  const data = (await api.post<ImportReport>(`${IMPORT_BASE}/validate`, { document, create_missing: createMissing, skip_existing: skipExisting })).data;
  return { ...data, errors: data?.errors ?? [], items: Array.isArray(data?.items) ? data.items : [] };
}

export async function commitImport(document: unknown, filename: string | null, createMissing: boolean, skipExisting = false): Promise<ImportBatch> {
  return (await api.post<ImportBatch>(`${IMPORT_BASE}/commit`, { document, filename, create_missing: createMissing, skip_existing: skipExisting })).data;
}

export async function generateWithClaude(data: {
  level: LmsLevel;
  module: number;
  lesson: number;
  topic: string;
  skills: SkillKey[];
  notes?: string | null;
}): Promise<{ document: Record<string, unknown>; report: ImportReport }> {
  return (await api.post<{ document: Record<string, unknown>; report: ImportReport }>(`${IMPORT_BASE}/generate`, data, { timeout: 240000 })).data;
}

export async function listImportBatches(): Promise<ImportBatch[]> {
  const data = (await api.get<ImportBatch[]>(`${IMPORT_BASE}/batches`)).data;
  return Array.isArray(data) ? data : [];
}

export async function getImportBatch(id: string): Promise<ImportBatch> {
  return (await api.get<ImportBatch>(`${IMPORT_BASE}/batches/${id}`)).data;
}

export async function publishImportBatch(id: string): Promise<ImportBatch> {
  return (await api.post<ImportBatch>(`${IMPORT_BASE}/batches/${id}/publish`)).data;
}

/** Browser download of a JSON value (schema, example). */
export function downloadJson(value: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
