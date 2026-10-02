// VIZU-Multilevel Admin Dashboard — mirrors backend/app/schemas/vizu_multilevel/admin_schema.py

export interface VizuMultilevelOverviewStats {
  total_attempts: number;
  today_attempts: number;
  week_attempts: number;
  month_attempts: number;
  completed_attempts: number;
  in_progress_attempts: number;
  average_score_percent: number | null;
  most_common_level: string | null;
}

export interface VizuMultilevelActivityPoint {
  label: string;
  started: number;
  completed: number;
}

export interface VizuMultilevelActivityStats {
  days: number;
  points: VizuMultilevelActivityPoint[];
  completion_rate_percent: number | null;
  average_duration_minutes: number | null;
}

export interface VizuMultilevelLevelBucket {
  level: string;
  count: number;
  percent: number;
}

export interface VizuMultilevelCompetencyStat {
  skill: "LESEN" | "HOEREN" | "SCHREIBEN" | "SPRECHEN";
  average_percent: number | null;
  submitted_count: number;
  most_common_level: string | null;
}

export interface VizuMultilevelLevelAnalytics {
  level_distribution: VizuMultilevelLevelBucket[];
  total_leveled: number;
  competencies: VizuMultilevelCompetencyStat[];
}

export interface VizuMultilevelTimeAnalytics {
  average_completion_minutes: number | null;
  abandonment_rate_percent: number | null;
}

export interface VizuMultilevelAnalytics {
  overview: VizuMultilevelOverviewStats;
  activity_7d: VizuMultilevelActivityStats;
  activity_30d: VizuMultilevelActivityStats;
  level_analytics: VizuMultilevelLevelAnalytics;
  time_analytics: VizuMultilevelTimeAnalytics;
}

export interface VizuMultilevelAdminAttemptItem {
  id: string;
  user_id: string;
  student_name: string;
  username: string;
  email: string;
  status: "IN_PROGRESS" | "COMPLETED";
  started_at: string;
  completed_at: string | null;
  duration_minutes: number | null;
  lesen_level: string | null;
  hoeren_level: string | null;
  schreiben_level: string | null;
  sprechen_level: string | null;
  overall_level: string | null;
  lesen_score: number | null;
  hoeren_score?: number | null;
  schreiben_score?: number | null;
  sprechen_score?: number | null;
}

export interface VizuMultilevelAdminAttemptsPage {
  items: VizuMultilevelAdminAttemptItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface VizuMultilevelHoerenAudioSlot {
  aufgabe_number: number;
  audio_id: string | null;
  has_audio: boolean;
  file_name: string | null;
  content_type: string | null;
  duration_seconds: number | null;
  is_active: boolean;
  updated_at: string | null;
}

// Lesen / Hören content authoring — the ADMIN view of an Aufgabe: unlike
// the student-facing shape it carries the CEFR level, publish state, the
// Hören transcript and which option is correct.
export interface VizuMultilevelAdminOption {
  id: string;
  option_text: string;
  is_correct: boolean;
  order_index: number;
}

export interface VizuMultilevelAdminQuestion {
  id: string;
  question_type: string;
  passage_text: string | null;
  prompt: string;
  order_index: number;
  points: number;
  is_active: boolean;
  options: VizuMultilevelAdminOption[];
}

export interface VizuMultilevelContentTask {
  id: string;
  skill: "LESEN" | "HOEREN";
  level: string;
  order_index: number;
  passage_text: string | null;
  transcript: string | null;
  is_published: boolean;
  audio_url: string | null;
  questions: VizuMultilevelAdminQuestion[];
}

export interface VizuMultilevelContentTaskPayload {
  level?: string;
  order_index?: number;
  passage_text?: string | null;
  transcript?: string | null;
  is_published?: boolean;
}

export interface VizuMultilevelQuestionPayload {
  question_type: string;
  passage_text?: string | null;
  prompt: string;
  order_index: number;
  points: number;
  is_active?: boolean;
  options: { option_text: string; is_correct: boolean }[];
}

// Sprechen Aufgabe management
export interface VizuMultilevelSpeakingTaskAdmin {
  id: string;
  level: string;
  order_index: number;
  title: string;
  instruction: string;
  preparation_text: string | null;
  prep_seconds: number;
  max_seconds: number;
  points: number;
  is_active: boolean;
}

export type VizuMultilevelSpeakingTaskPayload = Partial<Omit<VizuMultilevelSpeakingTaskAdmin, "id">>;

// Statistics tab
export interface VizuMultilevelStatistics {
  total_attempts: number;
  completed_attempts: number;
  in_progress_attempts: number;
  abandoned_attempts: number;
  pending_review_attempts: number;
  results: { result: string; count: number }[];
  average_score_percent: number;
  competency_averages: { skill: string; average_percent: number; finished_count: number }[];
  completion_rate_percent: number;
}

// Schreiben Aufgabe management — full CRUD, unlike Lesen/Hören's
// read-only preview (this module explicitly asked for a real editor).
export interface VizuMultilevelWritingRubricCriterion {
  id: string | null;
  name: string;
  max_score: number;
  order_index: number;
}

export interface VizuMultilevelWritingTaskAdmin {
  id: string;
  level: string;
  order_index: number;
  title: string;
  instruction: string;
  min_words: number;
  max_words: number;
  image_url: string | null;
  points: number;
  is_active: boolean;
  rubric_criteria: VizuMultilevelWritingRubricCriterion[];
}

export type VizuMultilevelWritingTaskCreatePayload = Pick<
  VizuMultilevelWritingTaskAdmin,
  "level" | "order_index" | "title" | "instruction" | "min_words" | "max_words" | "points" | "is_active"
> & { image_url?: string | null; rubric_criteria?: VizuMultilevelWritingRubricCriterion[] };

export interface VizuMultilevelWritingTaskAdminPayload {
  level?: string;
  order_index?: number;
  title?: string;
  instruction?: string;
  min_words?: number;
  max_words?: number;
  image_url?: string | null;
  points?: number;
  is_active?: boolean;
  rubric_criteria?: VizuMultilevelWritingRubricCriterion[];
}
