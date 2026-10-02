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
  /** Set when a finished attempt is not kept as a result (BELOW_A1 / NO_CONTENT). */
  discarded_reason?: string | null;
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
  /** The audio itself is fetched through an authenticated endpoint — the
   * client never receives a URL, file name or storage path. */
  has_audio: boolean;
  questions: VizuMultilevelQuestion[];
}

export interface VizuMultilevelHoerenResult {
  attempt_id: string;
  total_points: number;
  max_points: number;
  correct: number;
  wrong: number;
  unanswered: number;
  /** Determined by the server from the score; null = below A1. */
  hoeren_level: string | null;
  below_a1: boolean;
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
  /** Recommended speaking time (hint) … max_seconds (recording stops automatically). */
  min_seconds: number;
  max_seconds: number;
  points: number;
}

/** Server pipeline of one saved answer (null = recorded before the AI pipeline). */
export type VizuMultilevelSpeakingStatus = "PROCESSING" | "TRANSCRIBED" | "EVALUATING" | "EVALUATED" | "FAILED";

export interface VizuMultilevelSpeakingSubmission {
  id: string;
  task_id: string;
  duration_seconds: number | null;
  submitted_at: string | null;
  status: VizuMultilevelSpeakingStatus | null;
}

export interface VizuMultilevelSpeakingTaskEvaluation {
  task_id: string;
  order_index: number;
  title: string;
  score: number;
  max_score: number;
  answered: boolean;
  transcript: string | null;
  criteria: { key: string; label: string; score: number; max: number }[];
  strengths: string[];
  improvements: string[];
  errors: { original: string; correction: string; explanation: string }[];
  feedback: string;
  next_step: string;
  teacher_comment: string | null;
}

export interface VizuMultilevelSpeakingEvaluation {
  status: "NOT_SUBMITTED" | "PENDING" | "DONE" | "FAILED";
  evaluated: number;
  total_tasks: number;
  progress: { task_id: string; order_index: number; status: VizuMultilevelSpeakingStatus | null }[];
  total_score: number | null;
  max_score: number;
  /** Only in the final result: A1..C1 or "BELOW_A1". */
  level: string | null;
  tasks: VizuMultilevelSpeakingTaskEvaluation[];
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

export interface VizuMultilevelAvailability {
  lesen: number;
  hoeren: number;
  schreiben: number;
  sprechen: number;
  min_answers: number;
  available: boolean;
}

// ---- Schreiben AI evaluation (read-only; scores are computed server-side) ----

export interface VizuMultilevelWritingErrorItem {
  original: string;
  correction: string;
  explanation: string;
  category: string;
}

export interface VizuMultilevelWritingTaskEvaluation {
  task_id: string;
  order_index: number;
  title: string;
  score: number;
  max_score: number;
  word_count: number;
  criteria: { name: string; score: number; max: number; justification: string }[];
  strengths: string[];
  errors: VizuMultilevelWritingErrorItem[];
  feedback: string;
  next_steps: string[];
  /** Comments on this student's text per area (may be empty for older results). */
  grammar?: string;
  vocabulary?: string;
  task_fulfilment?: string;
  improvement?: string;
}

export interface VizuMultilevelWritingEvaluation {
  status: "NOT_SUBMITTED" | "PENDING" | "DONE" | "FAILED";
  evaluated: number;
  total_tasks: number;
  total_score: number | null;
  max_score: number;
  tasks: VizuMultilevelWritingTaskEvaluation[];
  summary: { good: string[]; improve: string[]; next: string[] } | null;
}
