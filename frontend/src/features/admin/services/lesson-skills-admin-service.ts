import type { AiEvaluationResult } from "@/components/lesson-player/common/ai-evaluation-card";
import type { LessonSkillResults } from "@/features/lessons/services/lesson-skills-service";
import { api } from "@/src/services/api";

import type { Speaking, Writing } from "../types/content.types";

const BASE = "/api/v1/admin/lesson-skills";

export type AdminQuestionType = "MULTIPLE_CHOICE" | "TRUE_FALSE" | "MATCHING" | "GAP_FILL" | "SHORT_ANSWER";

/** Zuordnung / Lückentext / Kurzantwort definition incl. answer key
 * (backend: app/services/lesson_skills/question_types.py). */
export interface AdminQuestionConfig {
  items?: { id: string; text: string }[];
  targets?: { id: string; text: string }[];
  pairs?: Record<string, string>;
  text?: string;
  gaps?: Record<string, { accepted: string[]; options?: string[] }>;
  accepted?: string[];
  case_sensitive?: boolean;
  max_length?: number;
}

export interface AdminOption {
  id?: string;
  text: string;
  is_correct: boolean;
}

export interface AdminQuestion {
  id?: string;
  question: string;
  question_type: AdminQuestionType;
  points: number;
  explanation: string | null;
  options: AdminOption[];
  config?: AdminQuestionConfig | null;
}

export interface AdminLesenText {
  id: string;
  title: string;
  content: string;
  order_index: number;
  is_published: boolean;
  questions: AdminQuestion[];
}

export interface AdminHoerenTask {
  id: string;
  lesson_id: string;
  title: string;
  audio_url: string | null;
  transcript: string | null;
  instruction: string | null;
  order_index: number;
  is_published: boolean;
  has_uploaded_audio: boolean;
  audio_duration_seconds: number | null;
  audio_content_type: string | null;
  audio_original_name: string | null;
  question_count: number;
  max_points: number;
  questions: AdminQuestion[];
}

export interface RubricCriterion {
  key: string;
  name: string;
  max: number;
}

export interface AiTaskSettings {
  ai_evaluation_enabled: boolean;
  ai_instructions: string | null;
  feedback_language: string;
  max_score: number;
  max_attempts: number;
  rubric: RubricCriterion[] | null;
}

export type WritingTextType = "message" | "email" | "letter" | "description" | "opinion" | "essay" | "report" | "other";

export type AdminWritingTask = Writing &
  AiTaskSettings & {
    text_type: WritingTextType | null;
    audience: string | null;
    time_limit_minutes: number | null;
    content_id: string | null;
    helper_words: string | null;
    image_url: string | null;
    opens_at: string | null;
    closes_at: string | null;
  };

export type AdminSpeakingTask = Speaking &
  AiTaskSettings & {
    min_duration_seconds: number;
    response_type: "MONOLOG" | "DIALOG";
    questions: string[] | null;
    speech_goal: string | null;
    content_id: string | null;
  };

export interface LessonSkillsOverview {
  lesson: { id: string; title: string; number: number; level: string };
  /** the level's default rubrics (applied when a task has no own rubric) */
  default_rubrics: { writing: RubricCriterion[]; speaking: RubricCriterion[] };
  lesen: AdminLesenText[];
  hoeren: AdminHoerenTask[];
  schreiben: AdminWritingTask[];
  sprechen: AdminSpeakingTask[];
}

export interface EvaluationHistoryEntry {
  id: string;
  source: "AI" | "MANUAL_OVERRIDE";
  status: string;
  score: number | null;
  error: string | null;
  model: string | null;
  actor_id: string | null;
  created_at: string;
  result: (AiEvaluationResult & { reason?: string; previous_score?: number | null }) | null;
}

export interface AdminSubmission {
  id: string;
  kind: "WRITING" | "SPEAKING";
  task_id: string;
  task_title: string;
  user_id: string;
  student_name: string;
  status: string;
  score: number | null;
  ai_score: number | null;
  feedback: string | null;
  ai_evaluation: AiEvaluationResult | null;
  evaluation_error: string | null;
  attempt_count: number;
  submitted_at: string | null;
  evaluated_at: string | null;
  reviewed_at: string | null;
  history: EvaluationHistoryEntry[];
  answer_text?: string | null;
  transcript?: string | null;
  duration_seconds?: number | null;
  has_audio?: boolean;
}

export type AdminStudentResult = Omit<LessonSkillResults, "lesson_id"> & {
  user_id: string;
  student_name: string;
  email: string | null;
};

export interface LessonSkillsAdminResults {
  students: AdminStudentResult[];
  submissions: AdminSubmission[];
}

/** "writing" | "speaking" in the URL, WRITING | SPEAKING in the payloads. */
export function kindPath(kind: AdminSubmission["kind"]): "writing" | "speaking" {
  return kind === "WRITING" ? "writing" : "speaking";
}

export async function getLessonSkillsOverview(lessonId: string): Promise<LessonSkillsOverview> {
  return (await api.get<LessonSkillsOverview>(`${BASE}/lessons/${lessonId}`)).data;
}

export async function saveQuestions(kind: "readings" | "listenings", id: string, questions: AdminQuestion[]) {
  return (await api.put<{ id: string; questions: AdminQuestion[] }>(`${BASE}/${kind}/${id}/questions`, { questions })).data;
}

export async function uploadListeningAudio(listeningId: string, file: File, durationSeconds: number | null) {
  const form = new FormData();
  form.append("file", file);
  if (durationSeconds) form.append("duration_seconds", String(Math.round(durationSeconds)));
  return (await api.post(`${BASE}/listenings/${listeningId}/audio`, form, { headers: { "Content-Type": "multipart/form-data" } })).data;
}

export async function getListeningAudioBlobUrl(listeningId: string): Promise<string> {
  const response = await api.get(`${BASE}/listenings/${listeningId}/audio`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

export async function duplicateItem(kind: "readings" | "listenings" | "writings" | "speakings", id: string) {
  return (await api.post<{ id: string }>(`${BASE}/${kind}/${id}/duplicate`)).data;
}

export async function getLessonSkillsResults(lessonId: string): Promise<LessonSkillsAdminResults> {
  return (await api.get<LessonSkillsAdminResults>(`${BASE}/lessons/${lessonId}/results`)).data;
}

export async function overrideSubmissionScore(
  kind: AdminSubmission["kind"],
  submissionId: string,
  data: { score: number; feedback?: string | null; reason?: string | null },
): Promise<AdminSubmission> {
  return (await api.put<AdminSubmission>(`${BASE}/submissions/${kindPath(kind)}/${submissionId}/score`, data)).data;
}

export async function reevaluateSubmission(kind: AdminSubmission["kind"], submissionId: string) {
  return (await api.post<{ id: string; status: string }>(`${BASE}/submissions/${kindPath(kind)}/${submissionId}/evaluate`)).data;
}

/** The submitted recording (admin may listen to every submission). */
export async function getSpeakingAudioBlobUrl(submissionId: string): Promise<string> {
  const response = await api.get(`/api/v1/speakings/submissions/${submissionId}/audio`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

/** Server error code / message of an axios error ({success:false, message}). */
export function apiErrorMessage(err: unknown, fallback: string): string {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  const message = data?.message ?? data?.detail;
  if (typeof message === "string" && message) return message;
  if (Array.isArray(message)) return fallback;
  return fallback;
}
