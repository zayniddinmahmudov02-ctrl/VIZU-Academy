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
  /** questions still waiting for their answer key (block publishing) */
  key_missing?: number;
  questions: AdminQuestion[];
}

export type ExerciseSkill = "GRAMMATIK" | "WORTSCHATZ" | "UEBUNGEN" | "YAKUNIY";

export interface AdminExercise {
  id: string;
  lesson_id: string;
  skill: ExerciseSkill;
  title: string;
  instruction: string | null;
  order_index: number;
  is_published: boolean;
  /** "book" = from the course book, "vizu" = created by VIZU */
  source: "book" | "vizu";
  content_id: string | null;
  question_count: number;
  max_points: number;
  questions: AdminQuestion[];
}

export interface AdminGrammar {
  id: string;
  lesson_id: string;
  title: string;
  content: string;
  order_index: number;
  is_published: boolean;
  content_id: string | null;
}

export interface AdminWord {
  id: string;
  lesson_id: string;
  german_word: string;
  article: string | null;
  plural: string | null;
  translation: string;
  example_sentence: string | null;
  example_translation: string | null;
  order_index: number;
  is_published: boolean;
  content_id: string | null;
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
    task_kind?: "SPRECHEN" | "FRAGE";
  };

export interface LessonSkillsOverview {
  lesson: { id: string; title: string; number: number; level: string };
  /** the level's default rubrics (applied when a task has no own rubric) */
  default_rubrics: { writing: RubricCriterion[]; speaking: RubricCriterion[] };
  lesen: AdminLesenText[];
  hoeren: AdminHoerenTask[];
  schreiben: AdminWritingTask[];
  sprechen: AdminSpeakingTask[];
  frage: AdminSpeakingTask[];
  grammatik: AdminGrammar[];
  wortschatz: AdminWord[];
  exercises: AdminExercise[];
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

export async function saveQuestions(kind: "readings" | "listenings" | "exercises", id: string, questions: AdminQuestion[]) {
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

export async function duplicateItem(kind: "readings" | "listenings" | "writings" | "speakings" | "exercises", id: string) {
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
const KNOWN_ERRORS: Record<string, string> = {
  AUDIO_REQUIRED_TO_PUBLISH: "Zuerst das Audio hochladen — ohne Audio kann die Hören-Aufgabe nicht veröffentlicht werden.",
  ANSWER_KEY_REQUIRED_TO_PUBLISH: "Zuerst für jede Frage die richtige Antwort festlegen (Fragen → nach dem Anhören des Audios).",
  NO_QUESTIONS: "Ohne Fragen kann die Übung nicht veröffentlicht werden.",
  KEY_REQUIRED: "Jede Frage braucht zuerst eine Lösung.",
};

export function apiErrorMessage(err: unknown, fallback: string): string {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  const message = data?.message ?? data?.detail;
  if (typeof message === "string" && message) return KNOWN_ERRORS[message] ?? message;
  if (Array.isArray(message)) return fallback;
  return fallback;
}

// ---------- exercise sets (Grammatik / Wortschatz / Yakuniy Test) ----------

export type ExerciseInput = Partial<Pick<AdminExercise, "title" | "instruction" | "order_index" | "is_published" | "source">> & { skill?: ExerciseSkill };

export async function createExercise(lessonId: string, data: ExerciseInput & { skill: ExerciseSkill; title: string }) {
  return (await api.post<AdminExercise>(`${BASE}/lessons/${lessonId}/exercises`, data)).data;
}

export async function updateExercise(id: string, data: ExerciseInput) {
  return (await api.put<AdminExercise>(`${BASE}/exercises/${id}`, data)).data;
}

export async function deleteExercise(id: string) {
  return (await api.delete(`${BASE}/exercises/${id}`)).data;
}

// ---------- Grammatik rules ----------

export interface GrammarInput {
  title: string;
  content: string;
  order_index: number;
  is_published: boolean;
}

export async function saveGrammar(lessonId: string, data: GrammarInput, id?: string) {
  return id
    ? (await api.put<AdminGrammar>(`${BASE}/grammars/${id}`, data)).data
    : (await api.post<AdminGrammar>(`${BASE}/lessons/${lessonId}/grammars`, data)).data;
}

export async function deleteGrammar(id: string) {
  return (await api.delete(`${BASE}/grammars/${id}`)).data;
}

// ---------- Wortschatz words ----------

export interface WordInput {
  german_word: string;
  translation: string;
  article: string | null;
  plural: string | null;
  example_sentence: string | null;
  example_translation: string | null;
  order_index?: number | null;
  is_published: boolean;
}

export async function saveWord(lessonId: string, data: WordInput, id?: string) {
  return id
    ? (await api.put<AdminWord>(`${BASE}/words/${id}`, data)).data
    : (await api.post<AdminWord>(`${BASE}/lessons/${lessonId}/words`, data)).data;
}

export async function deleteWord(id: string) {
  return (await api.delete(`${BASE}/words/${id}`)).data;
}
