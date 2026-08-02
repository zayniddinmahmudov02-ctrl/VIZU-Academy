// Mirrors backend/app/schemas/mock_exam/schema.py exactly — every field
// name/optionality here must match that file field-for-field.

export const KOMPETENZ_TYPES = ["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"] as const;
export type KompetenzType = (typeof KOMPETENZ_TYPES)[number];

export const QUESTION_TYPES = [
  "SINGLE_CHOICE",
  "MULTIPLE_CHOICE",
  "TRUE_FALSE",
  "MATCHING",
  "ORDERING",
  "FILL_BLANK",
  "DROPDOWN",
] as const;
export type QuestionType = (typeof QUESTION_TYPES)[number];

export const MODEL_TEST_STATUSES = ["DRAFT", "PUBLISHED", "ARCHIVED"] as const;
export type ModelTestStatus = (typeof MODEL_TEST_STATUSES)[number];

// ============================================================
// Certification Provider (Certificates)
// ============================================================

export interface CertificationProvider {
  id: string;
  name: string;
  code: string;
  logo_url: string | null;
  description: string | null;
  color: string | null;
  is_active: boolean;
  sort_order: number;
}

export type CertificationProviderCreate = Omit<CertificationProvider, "id">;
export type CertificationProviderUpdate = Partial<CertificationProviderCreate>;

// ============================================================
// Mock Exam Level
// ============================================================

export interface MockExamLevel {
  id: string;
  provider_id: string;
  level: string;
  title: string | null;
  description: string | null;
  sort_order: number;
  is_active: boolean;
}

export type MockExamLevelCreate = Omit<MockExamLevel, "id">;
export type MockExamLevelUpdate = Partial<Omit<MockExamLevel, "id" | "provider_id">>;

// ============================================================
// Model Test
// ============================================================

export interface ModelTest {
  id: string;
  level_id: string;
  title: string;
  description: string | null;
  status: ModelTestStatus;
  sort_order: number;
}

export type ModelTestCreate = Omit<ModelTest, "id">;
export type ModelTestUpdate = Partial<Omit<ModelTest, "id" | "level_id">>;

export interface ModelTestScore {
  model_test_id: string;
  total_points: number;
  kompetenz_points: Record<string, number>;
}

// ============================================================
// Kompetenz
// ============================================================

export interface Kompetenz {
  id: string;
  model_test_id: string;
  type: KompetenzType;
  title: string;
  description: string | null;
  total_points: number;
  duration_minutes: number;
  sort_order: number;
}

export type KompetenzCreate = Omit<Kompetenz, "id">;
export type KompetenzUpdate = Partial<Omit<Kompetenz, "id" | "model_test_id" | "type">>;

// ============================================================
// Teil
// ============================================================

export interface Teil {
  id: string;
  kompetenz_id: string;
  title: string;
  description: string | null;
  instructions: string | null;
  points: number;
  time_limit_minutes: number | null;
  sort_order: number;
}

export type TeilCreate = Omit<Teil, "id">;
export type TeilUpdate = Partial<Omit<Teil, "id" | "kompetenz_id">>;

// ============================================================
// Reading Content (Lesen)
// ============================================================

export interface ReadingContent {
  id: string;
  teil_id: string;
  content_type: "TEXT" | "IMAGE" | "TEXT_IMAGE";
  text: string | null;
  image_url: string | null;
}

export type ReadingContentCreate = Omit<ReadingContent, "id">;
export type ReadingContentUpdate = Partial<Omit<ReadingContent, "id" | "teil_id">>;

// ============================================================
// Listening Content (Hören)
// ============================================================

export interface ListeningContent {
  id: string;
  teil_id: string;
  audio_url: string;
  image_url: string | null;
  transcript: string | null;
}

export type ListeningContentCreate = Omit<ListeningContent, "id">;
export type ListeningContentUpdate = Partial<Omit<ListeningContent, "id" | "teil_id">>;

// ============================================================
// Writing Task (Schreiben)
// ============================================================

export interface WritingTask {
  id: string;
  teil_id: string;
  task_text: string;
  image_url: string | null;
  reference_document_url: string | null;
  word_limit: number | null;
  time_limit_minutes: number | null;
  points: number;
  difficulty: string | null;
  max_points: number;
  evaluation_rubric: string | null;
  passing_score: number;
}

export type WritingTaskCreate = Omit<WritingTask, "id">;
export type WritingTaskUpdate = Partial<Omit<WritingTask, "id" | "teil_id">>;

// ============================================================
// Speaking Task (Sprechen)
// ============================================================

export interface SpeakingTask {
  id: string;
  teil_id: string;
  task_text: string;
  image_url: string | null;
  preparation_time_seconds: number;
  speaking_time_seconds: number;
  max_recording_duration_seconds: number;
}

export type SpeakingTaskCreate = Omit<SpeakingTask, "id">;
export type SpeakingTaskUpdate = Partial<Omit<SpeakingTask, "id" | "teil_id">>;

// ============================================================
// Question Options
// ============================================================

export interface MockQuestionOption {
  id: string;
  question_id: string;
  option_text: string;
  match_value: string | null;
  is_correct: boolean;
  sort_order: number;
}

export type MockQuestionOptionCreate = Omit<MockQuestionOption, "id">;
export type MockQuestionOptionUpdate = Partial<Omit<MockQuestionOption, "id" | "question_id">>;

// ============================================================
// Questions (admin-facing — includes correct answers)
// ============================================================

export interface MockQuestion {
  id: string;
  reading_content_id: string | null;
  listening_content_id: string | null;
  question_type: QuestionType;
  question_text: string;
  explanation: string | null;
  correct_text_answer: string | null;
  points: number;
  sort_order: number;
  options: MockQuestionOption[];
}

export interface MockQuestionCreate {
  reading_content_id?: string | null;
  listening_content_id?: string | null;
  question_type: QuestionType;
  question_text: string;
  explanation?: string | null;
  correct_text_answer?: string | null;
  points?: number;
  sort_order?: number;
}

export type MockQuestionUpdate = Partial<
  Omit<MockQuestionCreate, "reading_content_id" | "listening_content_id">
>;

export interface MockQuestionMoveRequest {
  reading_content_id?: string | null;
  listening_content_id?: string | null;
}

// ============================================================
// Student Attempts / Submissions / Results
// ============================================================

export const ATTEMPT_STATUSES = ["IN_PROGRESS", "SUBMITTED", "GRADED"] as const;
export type AttemptStatus = (typeof ATTEMPT_STATUSES)[number];

export interface MockTestAttempt {
  id: string;
  model_test_id: string;
  user_id: string;
  status: AttemptStatus;
  started_at: string;
  submitted_at: string | null;
  total_score: number | null;
  max_score: number | null;
  time_spent_seconds: number;
}

export interface MockWritingSubmission {
  id: string;
  attempt_id: string;
  writing_task_id: string;
  answer_text: string;
  word_count: number;
  time_spent_seconds: number;
  ai_score: number | null;
  ai_grammar_score: number | null;
  ai_vocabulary_score: number | null;
  ai_structure_score: number | null;
  ai_task_achievement_score: number | null;
  ai_coherence_score: number | null;
  ai_feedback: string | null;
  teacher_score: number | null;
  teacher_feedback: string | null;
  submitted_at: string;
}

export interface MockWritingSubmissionTeacherUpdate {
  teacher_score?: number | null;
  teacher_feedback?: string | null;
}

export interface MockSpeakingSubmission {
  id: string;
  attempt_id: string;
  speaking_task_id: string;
  audio_url: string;
  transcript: string | null;
  ai_score: number | null;
  ai_feedback: string | null;
  teacher_score: number | null;
  teacher_feedback: string | null;
  submitted_at: string;
}

export interface MockSpeakingSubmissionTeacherUpdate {
  teacher_score?: number | null;
  teacher_feedback?: string | null;
}

// ============================================================
// Analytics
// ============================================================

export interface KompetenzAnalytics {
  kompetenz_id: string;
  type: string;
  title: string;
  average_score_percent: number;
  attempts: number;
}

export interface ModelTestAnalytics {
  model_test_id: string;
  title: string;
  average_score_percent: number;
  pass_rate_percent: number;
  attempts: number;
  kompetenzen: KompetenzAnalytics[];
}

export interface QuestionFailureItem {
  question_id: string;
  question_text: string;
  times_answered: number;
  times_correct: number;
  failure_rate_percent: number;
}

export interface CertificationProviderAnalytics {
  provider_id: string;
  name: string;
  average_score_percent: number;
  pass_rate_percent: number;
  total_attempts: number;
  model_tests: ModelTestAnalytics[];
  most_failed_questions: QuestionFailureItem[];
}

export interface DashboardSummary {
  certificates: number;
  levels: number;
  model_tests: number;
  questions: number;
  media_assets: number;
  students_attempted: number;
  total_attempts: number;
  ai_evaluations_used: number;
}
