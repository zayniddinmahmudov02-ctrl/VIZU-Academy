// Multilevel exam mode — mirrors backend/app/services/mock_exam/multilevel_exam_service.py (student + staff shapes).
// The student paper never carries keys; `is_correct` on options only appears in the admin preview.

export const EXAM_SECTIONS = ["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"] as const;
export type ExamSection = (typeof EXAM_SECTIONS)[number];
export type SectionStatus = "NOT_STARTED" | "OPEN" | "SUBMITTED" | "EXPIRED";
export type ResultLevel = "NICHT_BESTANDEN" | "B1" | "B2" | "C1" | "UNGEKLAERT" | "PENDING";

export interface SectionSummary {
  score: number | null;
  level: ResultLevel | null;
  status: SectionStatus;
  /** Lesen / Hören without any answer key: not scored */
  no_key?: boolean;
}

export interface AttemptSummary {
  attempt_id: string;
  status: "IN_PROGRESS" | "SUBMITTED" | "GRADED";
  started_at: string;
  submitted_at: string | null;
  total_score: number | null;
  max_score: number;
  result_level: ResultLevel | null;
  sections: Record<ExamSection, SectionSummary | null>;
  title?: string;
  duration_seconds?: number;
}

export interface ExamListItem {
  model_test_id: string;
  title: string;
  number: number;
  description: string | null;
  /** no Multilevel Premium (all 10 are locked until the purchase / promo is approved) */
  is_locked: boolean;
  /** PUBLISHED; false = "Tayyorlanmoqda" (shown, never startable) */
  available: boolean;
  attempts: number;
  open_attempt_id: string | null;
  /** the four sections with their server-side length; their sum is `total_minutes` (195 for the standard exam) */
  sections: { type: ExamSection; title: string; duration_minutes: number }[];
  total_minutes: number;
  state: "NEW" | "IN_PROGRESS" | "DONE" | "PREPARING";
  last_result: AttemptSummary | null;
}

export interface AttemptView {
  attempt_id: string;
  model_test_id: string;
  title: string;
  status: AttemptSummary["status"];
  started_at: string;
  finished: boolean;
  number?: number | null;
  total_minutes?: number;
  sections: {
    type: ExamSection;
    title: string;
    duration_minutes: number;
    /** what the server granted when the section was opened */
    duration_seconds?: number;
    status: SectionStatus;
    /** server clock: deadline - now, so a reload continues where the student was */
    remaining_seconds: number | null;
    started_at?: string | null;
    ended_at?: string | null;
    can_start: boolean;
  }[];
}

// ── answer keys (admin): the numbered table of one section, import check ──
export type KeySection = "LESEN" | "HOEREN";

export interface AnswerKeyItem {
  number: number;
  question_id: string;
  label: string;
  teil: string;
  type: string;
  option_count: number;
  /** the key as the admin typed it ("b", "R" …), or the one derived from the marked option */
  answer: string | null;
  source: "entered" | "derived" | null;
  option_text: string | null;
  editable: boolean;
}

export interface AnswerKeyTable {
  model_test_id: string;
  title: string;
  number: number;
  status: string;
  section: KeySection;
  question_count: number;
  keys_set: number;
  complete: boolean;
  attempts: number;
  items: AnswerKeyItem[];
  readiness: {
    ready: boolean; questions: number; keys_set: number; missing_keys: string[]; missing_audio: string[]; missing_sections: string[];
    /** Modelltest 1–6: missing keys / audio are warnings, publishing only needs complete sections */
    warn_only?: boolean; publishable?: boolean; warnings?: string[];
  };
}

export interface KeyImportResult {
  section: KeySection;
  expected: number;
  given: number;
  ok: boolean;
  applied: boolean;
  errors: { number: number | null; code: string; message: string }[];
  preview: { number: number; answer: string; option_text: string }[];
  table?: AnswerKeyTable;
}

export interface PaperOption {
  id: string;
  option_text: string;
  is_correct?: boolean;
}

export interface PaperQuestion {
  id: string;
  question_type: string;
  question_text: string;
  points: number;
  options: PaperOption[];
}

export interface PaperTeil {
  id: string;
  kind: "reading" | "listening" | "writing" | "speaking" | "empty";
  title: string;
  instructions: string | null;
  description: string | null;
  text: string | null;
  image_url: string | null;
  audio_url: string | null;
  /** the Teil plays no audio of its own: its Hören section has ONE shared audio (Modelltest 1) in `SectionPaper.shared_audio` */
  audio_shared?: boolean;
  writing_task: { id: string; task_text: string; word_limit: number | null; image_url: string | null; evaluation_rubric?: string | null } | null;
  speaking_task: {
    id: string;
    task_text: string;
    image_url: string | null;
    preparation_time_seconds: number;
    speaking_time_seconds: number;
    max_recording_duration_seconds: number;
  } | null;
  questions: PaperQuestion[];
}

/** the ONE audio of a shared-audio Hören section: signed stream URL + length (independent of the exam time) */
export interface SharedAudio {
  url: string;
  duration_ms: number | null;
  kompetenz_id: string;
}

export interface SectionPaper {
  attempt_id: string;
  section_type: ExamSection;
  title: string;
  remaining_seconds: number;
  deadline_at: string;
  teile: PaperTeil[];
  shared_audio?: SharedAudio | null;
  answers: Record<string, string[]>;
  writings: Record<string, string>;
  recordings: Record<string, string>;
}

export interface ReviewItem {
  question_id: string;
  question_text: string;
  chosen: string[];
  correct: string[];
  options: { id: string; option_text: string }[];
  is_correct: boolean;
  /** false: the question has no answer key yet — not graded */
  has_key?: boolean;
}

export interface ResultSection {
  type: ExamSection;
  title: string;
  score: number | null;
  max: number;
  level: ResultLevel | null;
  status: SectionStatus;
  raw_points: number | null;
  raw_max: number | null;
  /** Lesen / Hören without any answer key: not scored and not in the total */
  no_key?: boolean;
  awaiting_grading: boolean;
  feedback: string | null;
  review?: ReviewItem[];
  section_id?: string | null;
  /** where the score comes from (2026-11-28): the Lesen / Hören table, the AI or a Super Admin */
  score_source?: "AUTO" | "AI" | "MANUAL" | null;
  /** AI grading of Schreiben / Sprechen */
  ai_status?: "PENDING" | "RUNNING" | "DONE" | "FAILED" | "NEEDS_ADMIN" | null;
  ai_raw?: number | null;
  ai_raw_max?: number | null;
  evaluation?: AiEvaluationView | null;
}

/** One AI-graded Teil (Schreiben: score 0–max in 0.5 steps; Sprechen: six criteria 0–5). */
export interface AiTeil {
  teil: string;
  title: string;
  score: number;
  max: number;
  explanation?: string;
  criteria?: { key?: string; name: string; score?: number | null; max?: number; status?: string; comment: string }[];
  strengths?: string[];
  mistakes?: { original: string; correction: string; explanation?: string }[];
  recommendations?: string[];
  transcript?: string;
  answered?: boolean;
}

/** What the student / teacher see of the AI result (never the prompt or the model). */
export interface AiEvaluationView {
  raw: number;
  raw_max: number;
  converted: number | null;
  conversion_missing?: boolean;
  teile: AiTeil[];
  summary?: string;
  strengths?: string[];
  mistakes?: string[];
  recommendations?: string[];
  limitations?: string[];
  evaluated_at?: string;
}

export interface ScoreHistoryEntry {
  id: string;
  source: "AI" | "MANUAL_OVERRIDE";
  status: "SUCCEEDED" | "FAILED";
  score: number | null;
  created_at: string;
  actor: string | null;
  model: string | null;
  error: string | null;
  old_score: number | null;
  new_score: number | null;
  reason: string | null;
  raw: number | null;
  raw_max: number | null;
  cleared: boolean;
}

export interface AdminResultSection extends ResultSection {
  auto_score?: number | null;
  override_score?: number | null;
  ai_runs?: number;
  history?: ScoreHistoryEntry[];
  evaluation_full?: AiEvaluationView | null;
  conversion_missing?: boolean;
}

export interface ExamResult extends Omit<AttemptSummary, "sections"> {
  title: string;
  duration_seconds: number;
  result_rule: string | null;
  sections: ResultSection[];
}

export interface AdminAttemptDetail extends Omit<ExamResult, "sections"> {
  sections: AdminResultSection[];
  username: string | null;
  email: string | null;
  writings: { teil: string; task_text: string; word_limit: number | null; rubric: string | null; answer_text: string; word_count: number }[];
  recordings: { submission_id: string; teil: string; task_text: string; submitted_at: string }[];
}

export interface AdminAttemptRow extends AttemptSummary {
  title: string;
  username: string | null;
  email: string | null;
  duration_seconds: number;
}

export interface ExamStatistics {
  attempts: number;
  finished: number;
  graded: number;
  sections: Record<ExamSection, { count: number; average: number | null }>;
  levels: Partial<Record<ResultLevel, number>>;
  tests: { model_test_id: string; title: string; attempts: number; average_total: number | null }[];
}

export interface ScoringBands { B1: number; B2: number; C1: number }

export interface ScoringSettings {
  score_50: "UNGEKLAERT" | "B1" | "B2";
  overall_rule: "UNCONFIRMED" | "AVERAGE" | "LOWEST";
  /** level bands (lower bounds), owner's default B1 38 · B2 51 · C1 65 */
  bands: ScoringBands;
  /** 36 scores for 0–35 correct (Hören 30 is put on this 35 scale first) */
  lesen_table: number[];
  /** official Schreiben 36 → 75 rows [from, to, score]; raw scores outside every row wait for the Super Admin */
  schreiben_table: [number, number, number][];
  schreiben_missing?: [number, number][];
  defaults?: { bands: ScoringBands; lesen_table: number[]; schreiben_table: [number, number, number][] };
  schreiben_teil_max?: Record<string, number>;
  sprechen_criteria?: string[];
  sprechen_criterion_max?: number;
  score_50_choices?: string[];
  overall_rules?: string[];
  results_changed?: number;
}

export type ScoringSettingsUpdate = Partial<Pick<ScoringSettings, "overall_rule" | "bands" | "lesen_table" | "schreiben_table">>;

export interface ExamPreview {
  model_test_id: string;
  title: string;
  status: string;
  gaps: string[];
  sections: { type: ExamSection; title: string; duration_minutes: number; teile: PaperTeil[]; shared_audio?: SharedAudio | null }[];
}
