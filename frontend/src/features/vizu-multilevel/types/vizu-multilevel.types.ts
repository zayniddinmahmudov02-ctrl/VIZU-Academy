export type VizuMultilevelAttemptStatus = "IN_PROGRESS" | "COMPLETED";

export type VizuMultilevelSkill = "lesen" | "hoeren" | "schreiben" | "sprechen";

export interface VizuMultilevelAttempt {
  id: string;
  status: VizuMultilevelAttemptStatus;
  started_at: string;
  completed_at: string | null;
  lesen_score: number | null;
  lesen_level: string | null;
  hoeren_score: number | null;
  hoeren_level: string | null;
  schreiben_score: number | null;
  schreiben_level: string | null;
  schreiben_submitted_at: string | null;
  lesen_submitted_at: string | null;
  hoeren_submitted_at: string | null;
  sprechen_submitted_at: string | null;
  sprechen_score: number | null;
  sprechen_level: string | null;
  overall_level: string | null;
}

// ---- Server-authoritative section timing ----

export type VizuMultilevelSectionStatus = "LOCKED" | "AVAILABLE" | "RUNNING" | "SUBMITTED";

export interface VizuMultilevelSectionState {
  skill: VizuMultilevelSkill;
  status: VizuMultilevelSectionStatus;
  started_at: string | null;
  deadline_at: string | null;
  /** Computed by the server from its own clock — the client never derives
   * the remaining time from its own wall clock or from the start time. */
  seconds_remaining: number | null;
  duration_seconds: number;
  server_now: string;
  submitted: boolean;
}

export interface VizuMultilevelAttemptState {
  attempt_id: string;
  status: VizuMultilevelAttemptStatus;
  next_skill: VizuMultilevelSkill | null;
  server_now: string;
  sections: VizuMultilevelSectionState[];
}

// ---- Content (never carries a correct-answer field or a CEFR level —
// grading and levels are server-side only) ----

export type VizuMultilevelQuestionType = string;

export interface VizuMultilevelLesenResult {
  attempt_id: string;
  total_points: number;
  max_points: number;
  correct: number;
  wrong: number;
  unanswered: number;
  /** null = below A1 (not stored as a successful level). */
  lesen_level: string | null;
  below_a1: boolean;
}

export interface VizuMultilevelOption {
  id: string;
  option_text: string;
  order_index: number;
}

export interface VizuMultilevelQuestion {
  id: string;
  question_type: VizuMultilevelQuestionType;
  /** Set only when this question has its own passage, distinct from its
   * task's shared one — render this instead of the task's passage_text. */
  passage_text: string | null;
  prompt: string;
  order_index: number;
  points: number;
  options: VizuMultilevelOption[];
}

export interface VizuMultilevelTask {
  id: string;
  skill: string;
  order_index: number;
  passage_text: string | null;
  questions: VizuMultilevelQuestion[];
}

export interface VizuMultilevelHoerenTask {
  id: string;
  skill: string;
  order_index: number;
  passage_text: string | null;
  audio_url: string | null;
  questions: VizuMultilevelQuestion[];
}

export interface VizuMultilevelAnswerSubmit {
  question_id: string;
  /** null = left unanswered (scores 0 points). */
  option_id: string | null;
}

export interface VizuMultilevelWritingTask {
  id: string;
  order_index: number;
  title: string;
  instruction: string;
  min_words: number;
  max_words: number;
  image_url: string | null;
  points: number;
}

export interface VizuMultilevelWritingSubmission {
  task_id: string;
  content: string;
  word_count: number;
  status: "DRAFT" | "SUBMITTED";
}

export interface VizuMultilevelSpeakingTask {
  id: string;
  order_index: number;
  title: string;
  instruction: string;
  preparation_text: string | null;
  prep_seconds: number;
  max_seconds: number;
  points: number;
}

export interface VizuMultilevelSpeakingSubmission {
  id: string;
  task_id: string;
  duration_seconds: number | null;
  submitted_at: string | null;
}

// ---- Results ----

export type VizuMultilevelCompetencyStatus = "NO_CONTENT" | "NOT_SUBMITTED" | "PENDING_REVIEW" | "GRADED";

export interface VizuMultilevelCompetencyResult {
  skill: VizuMultilevelSkill;
  status: VizuMultilevelCompetencyStatus;
  raw_score: number | null;
  max_score: number | null;
  percentage: number | null;
  /** null on a GRADED competency = did not reach A1. */
  level: string | null;
}

export type VizuMultilevelOverallStatus = "NO_CONTENT" | "IN_PROGRESS" | "PENDING_REVIEW" | "FINAL" | "BELOW_A1";

export interface VizuMultilevelOverallResult {
  status: VizuMultilevelOverallStatus;
  level: string | null;
}

export interface VizuMultilevelAttemptResult {
  attempt_id: string;
  competencies: VizuMultilevelCompetencyResult[];
  overall: VizuMultilevelOverallResult;
}

export interface VizuMultilevelCompleteResponse {
  /** false = shown once, not kept in the student's history (below A1 / empty). */
  saved: boolean;
  result: VizuMultilevelAttemptResult;
}

export interface VizuMultilevelCertificate {
  attempt_id: string;
  student_name: string;
  issued_at: string | null;
  overall_level: string;
  competencies: VizuMultilevelCompetencyResult[];
}
