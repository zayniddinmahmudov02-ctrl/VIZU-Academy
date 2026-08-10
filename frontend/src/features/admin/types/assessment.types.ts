// Mirrors backend/app/schemas/assessment/*.py field-for-field. The
// universal Assessment engine: Assessment -> Section -> Task -> Question
// -> Option, shared by Course lessons (assessment_type=COURSE) and Mock
// Test / Vorbereitung (assessment_type=PREPARATION | MOCK_TEST) — one
// engine, not one per surface.

export const ASSESSMENT_TYPES = ["COURSE", "PREPARATION", "MOCK_TEST"] as const;
export type AssessmentType = (typeof ASSESSMENT_TYPES)[number];

export const ASSESSMENT_STATUSES = ["DRAFT", "PUBLISHED", "ARCHIVED"] as const;
export type AssessmentStatus = (typeof ASSESSMENT_STATUSES)[number];

// Section "skill" — reuses the same four values as the existing Kompetenz
// system (app/models/kompetenz.py) for naming consistency, even though
// this is a separate table.
export const SECTION_SKILLS = ["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"] as const;
export type SectionSkill = (typeof SECTION_SKILLS)[number];

export const TASK_TYPES = [
  "TRUE_FALSE",
  "MULTIPLE_CHOICE",
  "MULTIPLE_SELECT",
  "CLOZE_TEXT",
  "HEADING_MATCHING",
  "ADVERTISEMENT_MATCHING",
  "TEXT_MATCHING",
  "SENTENCE_ORDERING",
  "SHORT_ANSWER",
  "GAP_MATCHING",
  "DRAG_DROP",
  "CATEGORY_SORTING",
  "IMAGE_SELECTION",
  "WRITING",
  "SPEAKING",
] as const;
export type TaskType = (typeof TASK_TYPES)[number];

export const TASK_TYPE_LABELS: Record<TaskType, string> = {
  TRUE_FALSE: "Richtig/Falsch",
  MULTIPLE_CHOICE: "Multiple Choice",
  MULTIPLE_SELECT: "Mehrfachauswahl",
  CLOZE_TEXT: "Lückentext",
  HEADING_MATCHING: "Überschriften zuordnen",
  ADVERTISEMENT_MATCHING: "Anzeigen zuordnen",
  TEXT_MATCHING: "Texte zuordnen",
  SENTENCE_ORDERING: "Sätze ordnen",
  SHORT_ANSWER: "Kurzantwort",
  GAP_MATCHING: "Lücken zuordnen",
  DRAG_DROP: "Drag & Drop",
  CATEGORY_SORTING: "Kategorien sortieren",
  IMAGE_SELECTION: "Bildauswahl",
  WRITING: "Schreibaufgabe",
  SPEAKING: "Sprechaufgabe",
};

export const EVALUATION_MODES = ["AI_ONLY", "TEACHER_ONLY", "AI_AND_TEACHER"] as const;
export type EvaluationMode = (typeof EVALUATION_MODES)[number];

export const EVALUATION_MODE_LABELS: Record<EvaluationMode, string> = {
  AI_ONLY: "Nur KI",
  TEACHER_ONLY: "Nur Lehrer",
  AI_AND_TEACHER: "KI + Lehrer",
};

export const WRITING_SUBMISSION_STATUSES = ["DRAFT", "SUBMITTED", "PENDING_REVIEW", "GRADED"] as const;
export type WritingSubmissionStatus = (typeof WRITING_SUBMISSION_STATUSES)[number];

export type EvaluatorType = "AI" | "TEACHER";

export const SPEAKING_SUBMISSION_STATUSES = ["PENDING_REVIEW", "REVIEWED", "FINAL"] as const;
export type SpeakingSubmissionStatus = (typeof SPEAKING_SUBMISSION_STATUSES)[number];

export const ATTEMPT_STATUSES = ["IN_PROGRESS", "SUBMITTED", "GRADED"] as const;
export type AttemptStatus = (typeof ATTEMPT_STATUSES)[number];

export interface Assessment {
  id: string;
  title: string;
  description: string | null;
  assessment_type: AssessmentType;
  status: AssessmentStatus;
  lesson_id: string | null;
  language_id: string | null;
  level: string | null;
  attempt_limit: number | null;
  allow_retry: boolean;
  allow_edit: boolean;
  allow_resubmit: boolean;
  show_correct_answers: boolean;
  show_score: boolean;
  show_feedback: boolean;
  created_at: string;
}

export interface AssessmentCreate {
  title: string;
  description?: string | null;
  assessment_type: AssessmentType;
  lesson_id?: string | null;
  language_id?: string | null;
  level?: string | null;
  attempt_limit?: number | null;
  allow_retry?: boolean;
  allow_edit?: boolean;
  allow_resubmit?: boolean;
  show_correct_answers?: boolean;
  show_score?: boolean;
  show_feedback?: boolean;
}

export type AssessmentUpdate = Partial<AssessmentCreate & { status: AssessmentStatus }>;

export interface AssessmentSection {
  id: string;
  assessment_id: string;
  skill: SectionSkill;
  title: string;
  instructions: string | null;
  sort_order: number;
}

export interface AssessmentSectionCreate {
  assessment_id: string;
  skill: SectionSkill;
  title: string;
  instructions?: string | null;
  sort_order?: number;
}

export type AssessmentSectionUpdate = Partial<Omit<AssessmentSectionCreate, "assessment_id">>;

export interface TaskAudio {
  id: string;
  task_id: string;
  filename: string;
  format: "mp3" | "wav" | "m4a";
  duration_seconds: number | null;
  file_size_bytes: number;
}

// Audio play policy — only meaningful for HOEREN tasks; every other task
// type simply carries harmless defaults (audio_play_limit unset/allow_*
// all true) since it never has audio attached.
export interface AudioPolicy {
  audio_play_limit: number | null; // 1, 2, or null = unlimited
  allow_pause: boolean;
  allow_seek: boolean;
  allow_replay: boolean;
  allow_speed_change: boolean;
}

// Writing (SCHREIBEN) rubric criterion — admin-defined, never hardcoded.
export interface WritingRubricCriterion {
  id: string;
  task_id: string;
  name: string;
  max_score: number;
  sort_order: number;
}

export interface WritingRubricCriterionCreate {
  name: string;
  max_score?: number;
  sort_order?: number;
}

export type WritingRubricCriterionUpdate = Partial<WritingRubricCriterionCreate>;

export interface WritingConfig {
  image_url: string | null;
  min_words: number | null;
  max_words: number | null;
  time_limit_minutes: number | null;
  evaluation_mode: EvaluationMode;
}

export interface SpeakingConfig {
  prep_seconds: number | null;
  speak_seconds: number | null;
}

export interface AssessmentTask extends AudioPolicy, WritingConfig, SpeakingConfig {
  id: string;
  section_id: string;
  task_type: TaskType;
  title: string;
  instructions: string | null;
  content: string | null;
  config: string | null;
  max_points: number;
  sort_order: number;
  audio: TaskAudio | null;
  questions: TaskQuestion[];
  rubric_criteria: WritingRubricCriterion[];
}

export interface AssessmentTaskCreate extends Partial<AudioPolicy>, Partial<WritingConfig>, Partial<SpeakingConfig> {
  section_id: string;
  task_type: TaskType;
  title: string;
  instructions?: string | null;
  content?: string | null;
  config?: string | null;
  max_points?: number;
  sort_order?: number;
}

export type AssessmentTaskUpdate = Partial<Omit<AssessmentTaskCreate, "section_id" | "task_type">>;

export interface AudioPlayStatus {
  task_id: string;
  play_limit: number | null;
  plays_used: number;
  plays_remaining: number | null;
  can_play: boolean;
  allow_pause: boolean;
  allow_seek: boolean;
  allow_replay: boolean;
  allow_speed_change: boolean;
}

export interface TaskQuestion {
  id: string;
  task_id: string;
  prompt: string;
  correct_text_answer: string | null;
  alternative_answers: string | null;
  case_sensitive: boolean;
  points: number;
  sort_order: number;
  options: TaskOption[];
}

export interface TaskQuestionCreate {
  task_id: string;
  prompt: string;
  correct_text_answer?: string | null;
  alternative_answers?: string | null;
  case_sensitive?: boolean;
  points?: number;
  sort_order?: number;
}

export type TaskQuestionUpdate = Partial<Omit<TaskQuestionCreate, "task_id">>;

export interface TaskOption {
  id: string;
  question_id: string;
  option_text: string;
  match_value: string | null;
  is_correct: boolean;
  sort_order: number;
}

export interface TaskOptionCreate {
  question_id: string;
  option_text: string;
  match_value?: string | null;
  is_correct?: boolean;
  sort_order?: number;
}

export type TaskOptionUpdate = Partial<Omit<TaskOptionCreate, "question_id">>;

// ============================================================
// Public / attempt-taking (student-facing — never includes is_correct,
// correct_text_answer, or match_value on options for un-submitted tasks)
// ============================================================

export interface PublicTaskOption {
  id: string;
  option_text: string;
  sort_order: number;
}

export interface PublicTaskQuestion {
  id: string;
  prompt: string;
  points: number;
  sort_order: number;
  options: PublicTaskOption[];
}

export interface PublicWritingRubricCriterion {
  id: string;
  name: string;
  max_score: number;
  sort_order: number;
}

export interface PublicTask extends AudioPolicy {
  id: string;
  task_type: TaskType;
  title: string;
  instructions: string | null;
  content: string | null;
  config: string | null;
  max_points: number;
  sort_order: number;
  has_audio: boolean;
  audio_duration_seconds: number | null;
  image_url: string | null;
  min_words: number | null;
  max_words: number | null;
  time_limit_minutes: number | null;
  prep_seconds: number | null;
  speak_seconds: number | null;
  rubric_criteria: PublicWritingRubricCriterion[];
  questions: PublicTaskQuestion[];
}

export interface PublicSection {
  id: string;
  skill: SectionSkill;
  title: string;
  instructions: string | null;
  sort_order: number;
  tasks: PublicTask[];
}

export interface PublicAssessment {
  id: string;
  title: string;
  description: string | null;
  allow_edit: boolean;
  allow_resubmit: boolean;
  sections: PublicSection[];
}

export interface AssessmentAttempt {
  id: string;
  assessment_id: string;
  user_id: string;
  status: AttemptStatus;
  attempt_number: number;
  locked: boolean;
  started_at: string;
  submitted_at: string | null;
}

export interface SubmitAnswerInput {
  question_id: string;
  answer_data: string;
}

export interface SectionResult {
  section_id: string;
  section_score: number;
  max_section_score: number;
  percentage: number;
}

export interface AssessmentResult {
  attempt_id: string;
  total_score: number;
  max_score: number;
  percentage: number;
  section_results: SectionResult[];
  show_correct_answers: boolean;
  show_feedback: boolean;
}

// ============================================================
// Writing (SCHREIBEN) submissions / evaluations
// ============================================================

export interface WritingSubmission {
  id: string;
  user_id: string;
  assessment_id: string;
  section_id: string;
  task_id: string;
  attempt_id: string;
  content: string;
  word_count: number;
  character_count: number;
  status: WritingSubmissionStatus;
  submitted_at: string | null;
  final_score: number | null;
}

export interface WritingEvaluation {
  id: string;
  submission_id: string;
  evaluator_type: EvaluatorType;
  reviewed_by_id: string | null;
  rubric_scores: Record<string, number>;
  total_score: number;
  feedback: string | null;
  strengths: string | null;
  errors: string[];
  suggestions: string[];
  created_at: string;
}

export interface WritingResult {
  submission: WritingSubmission;
  evaluations: WritingEvaluation[];
  show_feedback: boolean;
}

export interface TeacherReviewInput {
  rubric_scores: Record<string, number>;
  feedback?: string | null;
}

export interface PendingWritingReviewItem {
  submission: WritingSubmission;
  task_title: string;
  student_name: string;
  rubric_criteria: WritingRubricCriterion[];
  ai_evaluation: WritingEvaluation | null;
}

// ============================================================
// Speaking (SPRECHEN) submissions / evaluations
// ============================================================

export interface SpeakingSubmission {
  id: string;
  user_id: string;
  assessment_id: string;
  section_id: string;
  task_id: string;
  attempt_id: string;
  filename: string;
  format: string;
  duration_seconds: number | null;
  file_size_bytes: number;
  status: SpeakingSubmissionStatus;
  submitted_at: string;
  final_score: number | null;
}

export interface SpeakingEvaluation {
  id: string;
  submission_id: string;
  reviewed_by_id: string | null;
  rubric_scores: Record<string, number>;
  total_score: number;
  feedback: string | null;
  created_at: string;
}

export interface SpeakingResult {
  submission: SpeakingSubmission;
  evaluations: SpeakingEvaluation[];
  show_feedback: boolean;
}

export interface SpeakingReviewInput {
  rubric_scores: Record<string, number>;
  feedback?: string | null;
  finalize: boolean;
}

export interface PendingSpeakingReviewItem {
  submission: SpeakingSubmission;
  task_title: string;
  student_name: string;
  rubric_criteria: WritingRubricCriterion[];
}
