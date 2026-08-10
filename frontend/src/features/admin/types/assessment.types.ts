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
};

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

export interface AssessmentTask {
  id: string;
  section_id: string;
  task_type: TaskType;
  title: string;
  instructions: string | null;
  content: string | null;
  config: string | null;
  max_points: number;
  sort_order: number;
  questions: TaskQuestion[];
}

export interface AssessmentTaskCreate {
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

export interface PublicTask {
  id: string;
  task_type: TaskType;
  title: string;
  instructions: string | null;
  content: string | null;
  config: string | null;
  max_points: number;
  sort_order: number;
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
