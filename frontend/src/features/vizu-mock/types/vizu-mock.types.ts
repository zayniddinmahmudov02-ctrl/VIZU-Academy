export type VizuMockAttemptStatus = "IN_PROGRESS" | "COMPLETED";

export type VizuMockSkill = "lesen" | "hoeren" | "schreiben" | "sprechen";

export interface VizuMockAttempt {
  id: string;
  status: VizuMockAttemptStatus;
  started_at: string;
  completed_at: string | null;
  // Real for Lesen (set once by POST .../lesen/submit); hoeren/schreiben/
  // sprechen/overall stay null until a future phase wires those modules
  // (see backend/app/models/vizu_mock_attempt.py) — never fabricated
  // client-side.
  lesen_score: number | null;
  lesen_level: string | null;
  hoeren_score: number | null;
  hoeren_level: string | null;
  schreiben_score: number | null;
  schreiben_level: string | null;
  schreiben_submitted_at: string | null;
  sprechen_level: string | null;
  overall_level: string | null;
}

// ---- Lesen content (never carries a correct-answer field — grading is
// server-side only, see POST .../lesen/submit) ----

export type VizuMockQuestionType = "TRUE_FALSE" | "MULTIPLE_CHOICE" | "CLOZE_TEXT";

export interface VizuMockOption {
  id: string;
  option_text: string;
  order_index: number;
}

export interface VizuMockQuestion {
  id: string;
  question_type: VizuMockQuestionType;
  /** Set only when this question has its own passage, distinct from its
   * task's shared one — render this instead of the task's passage_text
   * when present (A1/A2 content pairs each question with its own text;
   * B1-C1 content shares one passage across both of a task's questions). */
  passage_text: string | null;
  prompt: string;
  order_index: number;
  points: number;
  options: VizuMockOption[];
}

export interface VizuMockTask {
  id: string;
  skill: string;
  level: string;
  order_index: number;
  passage_text: string | null;
  questions: VizuMockQuestion[];
}

export interface VizuMockLevelScore {
  level: string;
  points: number;
  max_points: number;
  passed: boolean;
}

export interface VizuMockLesenResult {
  attempt_id: string;
  total_points: number;
  max_points: number;
  level_scores: VizuMockLevelScore[];
  lesen_level: string | null;
}

// ---- Hören content — same shape as Lesen's task/question/option types,
// plus `audio_url` (no passage_text is ever set; the source is audio,
// never a script/transcript sent to the client) ----

export interface VizuMockHoerenTask {
  id: string;
  skill: string;
  level: string;
  order_index: number;
  passage_text: string | null;
  audio_url: string | null;
  questions: VizuMockQuestion[];
}

export interface VizuMockHoerenResult {
  attempt_id: string;
  total_points: number;
  max_points: number;
  level_scores: VizuMockLevelScore[];
  hoeren_level: string | null;
}

// ---- Schreiben content — free-text, teacher-graded. No CEFR level or
// rubric is ever sent to the student (see backend's VizuMockWritingTaskPublic
// / VizuMockWritingSubmissionPublic schemas). ----

export interface VizuMockWritingTask {
  id: string;
  level: string;
  order_index: number;
  title: string;
  instruction: string;
  min_words: number;
  max_words: number;
  image_url: string | null;
  points: number;
}

export interface VizuMockWritingSubmission {
  task_id: string;
  content: string;
  word_count: number;
  status: "DRAFT" | "SUBMITTED";
}
