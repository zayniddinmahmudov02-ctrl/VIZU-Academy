import { api } from "@/src/services/api";

/** Lesen / Hören tests and the lesson's skill results
 * (backend: app/api/lesson_skills/router.py). Questions never contain the
 * answer key — it is only part of a SUBMITTED attempt's result. */

export type QuestionType = "MULTIPLE_CHOICE" | "TRUE_FALSE" | "MATCHING" | "GAP_FILL" | "SHORT_ANSWER";

/** option id (Multiple Choice, Richtig/Falsch), text (Kurzantwort) or
 * {item/gap id: value} (Zuordnung, Lückentext). */
export type AnswerValue = string | Record<string, string>;
export type Answers = Record<string, AnswerValue>;

/** Student view of a Zuordnung / Lückentext / Kurzantwort — never the key. */
export interface PublicQuestionConfig {
  items?: { id: string; text: string }[];
  targets?: { id: string; text: string }[];
  text?: string;
  gaps?: { id: string; options?: { id: string; text: string }[] }[];
  max_length?: number;
}

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
  config?: PublicQuestionConfig | null;
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
  /** config-based types: the given answer, the key and per item/gap correctness */
  answer?: AnswerValue | null;
  correct_answer?: AnswerValue | null;
  details?: Record<string, boolean> | null;
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
  /** main audio ("main") first, then labelled extra tracks — e.g. "Audio von Alisa" / "Audio von Alex" */
  audio_tracks?: HoerenAudioTrack[];
  questions: PublicQuestion[];
  transcript: string | null;
  summary: AttemptSummary;
  attempts: SkillAttempt[];
}

export interface HoerenAudioTrack {
  id: string;
  label: string | null;
  duration_seconds: number | null;
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
  /** Frage des Themas: the voice answer has been sent (it is not scored automatically) */
  submitted?: boolean;
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
  skills: Partial<Record<SkillKey, SkillResult>>;
  overall: {
    status: "final" | "interim" | "not_started" | "not_available";
    score: number | null;
    method: string | null;
    graded_skills: number;
    required_skills: number;
    weights?: Partial<Record<SkillKey, number>>;
    required?: SkillKey[];
  };
}

export type SkillKey = "frage" | "grammatik" | "lesen" | "hoeren" | "schreiben" | "sprechen" | "wortschatz" | "yakuniy";

export interface LevelProgressLesson {
  lesson_id: string;
  module_number: number;
  lesson_number: number;
  skills: Partial<Record<SkillKey, { status: SkillStatus; score: number | null }>>;
  overall: Pick<LessonSkillResults["overall"], "status" | "score" | "graded_skills" | "required_skills">;
}

export interface LevelProgress {
  level: string;
  lessons: LevelProgressLesson[];
}

const BASE = "/api/v1/lesson-skills";

export async function getLesenTest(lessonId: string): Promise<LesenTest> {
  return (await api.get<LesenTest>(`${BASE}/${lessonId}/lesen`)).data;
}

export async function startLesen(lessonId: string): Promise<SkillAttempt> {
  return (await api.post<SkillAttempt>(`${BASE}/${lessonId}/lesen/start`)).data;
}

export async function submitLesen(lessonId: string, attemptId: string, answers: Answers): Promise<AttemptResult> {
  return (await api.post<AttemptResult>(`${BASE}/${lessonId}/lesen/submit`, { attempt_id: attemptId, answers })).data;
}

export async function reviewLesen(lessonId: string, attemptId: string): Promise<AttemptResult> {
  return (await api.get<AttemptResult>(`${BASE}/${lessonId}/lesen/attempts/${attemptId}`)).data;
}

export async function getHoerenTasks(lessonId: string): Promise<HoerenTask[]> {
  return (await getHoerenSection(lessonId)).tasks;
}

/** Tasks with audio, plus how many published tasks still wait for their audio (shown as "not uploaded yet", never as a broken player). */
export async function getHoerenSection(lessonId: string): Promise<{ tasks: HoerenTask[]; audioPending: number }> {
  const data = (await api.get<{ tasks: HoerenTask[]; audio_pending?: number }>(`${BASE}/${lessonId}/hoeren`)).data;
  return { tasks: Array.isArray(data?.tasks) ? data.tasks : [], audioPending: data?.audio_pending ?? 0 };
}

export async function startHoeren(lessonId: string, listeningId: string): Promise<SkillAttempt> {
  return (await api.post<SkillAttempt>(`${BASE}/${lessonId}/hoeren/${listeningId}/start`)).data;
}

export async function submitHoeren(
  lessonId: string,
  listeningId: string,
  attemptId: string,
  answers: Answers,
): Promise<AttemptResult> {
  return (await api.post<AttemptResult>(`${BASE}/${lessonId}/hoeren/${listeningId}/submit`, { attempt_id: attemptId, answers })).data;
}

export async function reviewHoeren(lessonId: string, listeningId: string, attemptId: string): Promise<AttemptResult> {
  return (await api.get<AttemptResult>(`${BASE}/${lessonId}/hoeren/${listeningId}/attempts/${attemptId}`)).data;
}

/** The audio is never a public URL: fetched with the session, played from memory. */
export async function getHoerenAudioBlobUrl(lessonId: string, listeningId: string, trackId = "main"): Promise<string> {
  const path = trackId === "main" ? "audio" : `audio-tracks/${trackId}`;
  const response = await api.get(`${BASE}/${lessonId}/hoeren/${listeningId}/${path}`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

export async function getLessonSkillResults(lessonId: string): Promise<LessonSkillResults> {
  return (await api.get<LessonSkillResults>(`${BASE}/${lessonId}/results`)).data;
}

/** The caller's own skill status per lesson of one level (A1-C1). */
export async function getLevelProgress(level: string): Promise<LevelProgress> {
  const data = (await api.get<LevelProgress>(`${BASE}/levels/${level}/progress`)).data;
  return { level: data?.level ?? level, lessons: Array.isArray(data?.lessons) ? data.lessons : [] };
}

// ============================================================
// Exercise sets — Grammatik / Wortschatz practice, Yakuniy Test
// ============================================================

export type ExerciseSkill = "grammatik" | "wortschatz" | "uebungen" | "yakuniy" | "schreiben";

export interface ExerciseSet {
  id: string;
  title: string;
  instruction: string | null;
  /** "book" = from the course book, "vizu" = created from the lesson material */
  source: "book" | "vizu";
  questions: PublicQuestion[];
  summary: AttemptSummary;
  attempts: SkillAttempt[];
}

export async function getExercises(lessonId: string, skill: ExerciseSkill): Promise<ExerciseSet[]> {
  const data = (await api.get<{ exercises: ExerciseSet[] }>(`${BASE}/${lessonId}/exercises/${skill}`)).data;
  return Array.isArray(data?.exercises) ? data.exercises : [];
}

export async function startExercise(lessonId: string, skill: ExerciseSkill, exerciseId: string): Promise<SkillAttempt> {
  return (await api.post<SkillAttempt>(`${BASE}/${lessonId}/exercises/${skill}/${exerciseId}/start`)).data;
}

export async function submitExercise(lessonId: string, skill: ExerciseSkill, exerciseId: string, attemptId: string, answers: Answers): Promise<AttemptResult> {
  return (await api.post<AttemptResult>(`${BASE}/${lessonId}/exercises/${skill}/${exerciseId}/submit`, { attempt_id: attemptId, answers })).data;
}

export async function reviewExercise(lessonId: string, skill: ExerciseSkill, exerciseId: string, attemptId: string): Promise<AttemptResult> {
  return (await api.get<AttemptResult>(`${BASE}/${lessonId}/exercises/${skill}/${exerciseId}/attempts/${attemptId}`)).data;
}
