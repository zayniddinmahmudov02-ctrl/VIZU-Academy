// VIZU-Mock Admin Dashboard — mirrors backend/app/schemas/vizu_mock/admin_schema.py

export interface VizuMockOverviewStats {
  total_attempts: number;
  today_attempts: number;
  week_attempts: number;
  month_attempts: number;
  completed_attempts: number;
  in_progress_attempts: number;
  average_score_percent: number | null;
  most_common_level: string | null;
}

export interface VizuMockActivityPoint {
  label: string;
  started: number;
  completed: number;
}

export interface VizuMockActivityStats {
  days: number;
  points: VizuMockActivityPoint[];
  completion_rate_percent: number | null;
  average_duration_minutes: number | null;
}

export interface VizuMockLevelBucket {
  level: string;
  count: number;
  percent: number;
}

export interface VizuMockCompetencyStat {
  skill: "LESEN" | "HOEREN" | "SCHREIBEN" | "SPRECHEN";
  average_percent: number | null;
  submitted_count: number;
  most_common_level: string | null;
}

export interface VizuMockLevelAnalytics {
  level_distribution: VizuMockLevelBucket[];
  total_leveled: number;
  competencies: VizuMockCompetencyStat[];
}

export interface VizuMockTimeAnalytics {
  average_completion_minutes: number | null;
  abandonment_rate_percent: number | null;
}

export interface VizuMockAnalytics {
  overview: VizuMockOverviewStats;
  activity_7d: VizuMockActivityStats;
  activity_30d: VizuMockActivityStats;
  level_analytics: VizuMockLevelAnalytics;
  time_analytics: VizuMockTimeAnalytics;
}

export interface VizuMockAdminAttemptItem {
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
}

export interface VizuMockAdminAttemptsPage {
  items: VizuMockAdminAttemptItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface VizuMockAudio {
  id: string;
  title: string;
  audio_url: string;
  duration_seconds: number | null;
  task_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface VizuMockAudioCreatePayload {
  title: string;
  audio_url: string;
  duration_seconds?: number | null;
  task_id?: string | null;
}

export interface VizuMockAudioUpdatePayload {
  title?: string;
  audio_url?: string;
  duration_seconds?: number | null;
  task_id?: string | null;
  is_active?: boolean;
}

// Read-only Lesen content preview (subset of the student-facing shape)
export interface VizuMockAdminTask {
  id: string;
  skill: string;
  level: string;
  order_index: number;
  passage_text: string | null;
  questions: { id: string }[];
}

// Read-only Hören content preview — same shape, plus the task's
// currently-attached active audio URL (if any).
export interface VizuMockAdminHoerenTask {
  id: string;
  skill: string;
  level: string;
  order_index: number;
  passage_text: string | null;
  audio_url: string | null;
  questions: { id: string; points: number }[];
}

// Schreiben Aufgabe management — full CRUD, unlike Lesen/Hören's
// read-only preview (this module explicitly asked for a real editor).
export interface VizuMockWritingRubricCriterion {
  id: string | null;
  name: string;
  max_score: number;
  order_index: number;
}

export interface VizuMockWritingTaskAdmin {
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
  rubric_criteria: VizuMockWritingRubricCriterion[];
}

export interface VizuMockWritingTaskAdminPayload {
  level?: string;
  order_index?: number;
  title?: string;
  instruction?: string;
  min_words?: number;
  max_words?: number;
  image_url?: string | null;
  points?: number;
  is_active?: boolean;
  rubric_criteria?: VizuMockWritingRubricCriterion[];
}
