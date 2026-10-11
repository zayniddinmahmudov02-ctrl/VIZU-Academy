import { api } from "@/src/services/api";

/** Lesen / Hören tests and the lesson's skill results
 * (backend: app/api/lesson_skills/router.py). Questions never contain the
 * answer key — it is only part of a SUBMITTED attempt's result. */

export type QuestionType = "MULTIPLE_CHOICE" | "TRUE_FALSE";

export interface PublicOption {
  id: string;
  text: string;
}

export interface PublicQuestion {
  id: string;
  question: string;
  question_type: QuestionType;
  points: number;
  options: PublicOption[];
}

export interface SkillAttempt {
  id: string;
  attempt_number: number;
  status: "IN_PROGRESS" | "SUBMITTED";
  score: number | null;
  correct_count: number | null;
  question_count: number | null;
  started_at: string;
  submitted_at: string | null;
  duration_seconds: number | null;
}

export interface AttemptSummary {
  attempts_count: number;
  best_score: number | null;
  last_score: number | null;
  last_submitted_at: string | null;
  in_progress_attempt_id: string | null;
}

export interface QuestionResult {
  question_id: string;
  selected_option_id: string | null;
  correct_option_id: string | null;
  is_correct: boolean;
  points: number;
  max_points: number;
  explanation: string | null;
}

export interface AttemptResult {
  attempt: SkillAttempt;
  results: QuestionResult[];
  correct_count: number;
  question_count: number;
  points: number;
  max_points: number;
  score: number;
  transcript: string | null;
}

export interface LesenText {
  id: string;
  title: string;
  content: string;
  questions: PublicQuestion[];
}

export interface LesenTest {
  lesson_id: string;
  texts: LesenText[];
  question_count: number;
  summary: AttemptSummary;
  attempts: SkillAttempt[];
}

export interface HoerenTask {
  id: string;
  title: string;
  instruction: string | null;
  audio_duration_seconds: number | null;
  external_audio_url: string | null;
  questions: PublicQuestion[];
  transcript: string | null;
  summary: AttemptSummary;
  attempts: SkillAttempt[];
}

export type SkillStatus =
  | "not_available"
  | "not_started"
  | "in_progress"
  | "pending_evaluation"
  | "evaluation_failed"
  | "completed";

export interface SkillResultTask {
  id: string;
  title: string;
  status?: SkillStatus;
  score?: number | null;
  best_score?: number | null;
  attempts: number;
  max_attempts?: number;
  can_resubmit?: boolean;
}

export interface SkillResult {
  available: boolean;
  status: SkillStatus;
  score: number | null;
  interim?: boolean;
  attempts?: number;
  submitted_at?: string | null;
  evaluated_at?: string | null;
  tasks?: SkillResultTask[];
  can_retry?: boolean;
}

export interface LessonSkillResults {
  lesson_id: string;
  skills: Record<"lesen" | "hoeren" | "schreiben" | "sprechen", SkillResult>;
  overall: {
    status: "final" | "interim" | "not_started" | "not_available";
    score: number | null;
    method: string | null;
    graded_skills: number;
    required_skills: number;
  };
}

const BASE = "/api/v1/lesson-skills";

export async function getLesenTest(lessonId: string): Promise<LesenTest> {
  return (await api.get<LesenTest>(`${BASE}/${lessonId}/lesen`)).data;
}

export async function startLesen(lessonId: string): Promise<SkillAttempt> {
  return (await api.post<SkillAttempt>(`${BASE}/${lessonId}/lesen/start`)).data;
}

export async function submitLesen(lessonId: string, attemptId: string, answers: Record<string, string>): Promise<AttemptResult> {
  return (await api.post<AttemptResult>(`${BASE}/${lessonId}/lesen/submit`, { attempt_id: attemptId, answers })).data;
}

export async function reviewLesen(lessonId: string, attemptId: string): Promise<AttemptResult> {
  return (await api.get<AttemptResult>(`${BASE}/${lessonId}/lesen/attempts/${attemptId}`)).data;
}

export async function getHoerenTasks(lessonId: string): Promise<HoerenTask[]> {
  const data = (await api.get<{ tasks: HoerenTask[] }>(`${BASE}/${lessonId}/hoeren`)).data;
  return Array.isArray(data?.tasks) ? data.tasks : [];
}

export async function startHoeren(lessonId: string, listeningId: string): Promise<SkillAttempt> {
  return (await api.post<SkillAttempt>(`${BASE}/${lessonId}/hoeren/${listeningId}/start`)).data;
}

export async function submitHoeren(
  lessonId: string,
  listeningId: string,
  attemptId: string,
  answers: Record<string, string>,
): Promise<AttemptResult> {
  return (await api.post<AttemptResult>(`${BASE}/${lessonId}/hoeren/${listeningId}/submit`, { attempt_id: attemptId, answers })).data;
}

export async function reviewHoeren(lessonId: string, listeningId: string, attemptId: string): Promise<AttemptResult> {
  return (await api.get<AttemptResult>(`${BASE}/${lessonId}/hoeren/${listeningId}/attempts/${attemptId}`)).data;
}

/** The audio is never a public URL: fetched with the session, played from memory. */
export async function getHoerenAudioBlobUrl(lessonId: string, listeningId: string): Promise<string> {
  const response = await api.get(`${BASE}/${lessonId}/hoeren/${listeningId}/audio`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

export async function getLessonSkillResults(lessonId: string): Promise<LessonSkillResults> {
  return (await api.get<LessonSkillResults>(`${BASE}/${lessonId}/results`)).data;
}
