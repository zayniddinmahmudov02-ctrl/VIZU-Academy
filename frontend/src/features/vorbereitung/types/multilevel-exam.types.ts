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
  is_locked: boolean;
  attempts: number;
  open_attempt_id: string | null;
  /** the four sections with their server-side length; their sum is `total_minutes` (195 for the standard exam) */
  sections: { type: ExamSection; title: string; duration_minutes: number }[];
  total_minutes: number;
  state: "NEW" | "IN_PROGRESS" | "DONE";
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
  readiness: { ready: boolean; questions: number; keys_set: number; missing_keys: string[]; missing_audio: string[]; missing_sections: string[] };
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

export interface SectionPaper {
  attempt_id: string;
  section_type: ExamSection;
  title: string;
  remaining_seconds: number;
  deadline_at: string;
  teile: PaperTeil[];
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
  awaiting_grading: boolean;
  feedback: string | null;
  review?: ReviewItem[];
}

export interface ExamResult extends Omit<AttemptSummary, "sections"> {
  title: string;
  duration_seconds: number;
  result_rule: string | null;
  sections: ResultSection[];
}

export interface AdminAttemptDetail extends ExamResult {
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

export interface ScoringSettings {
  score_50: "UNGEKLAERT" | "B1" | "B2";
  overall_rule: "UNCONFIRMED" | "AVERAGE" | "LOWEST";
  score_50_choices?: string[];
  overall_rules?: string[];
  results_changed?: number;
}

export interface ExamPreview {
  model_test_id: string;
  title: string;
  status: string;
  gaps: string[];
  sections: { type: ExamSection; title: string; duration_minutes: number; teile: PaperTeil[] }[];
}
