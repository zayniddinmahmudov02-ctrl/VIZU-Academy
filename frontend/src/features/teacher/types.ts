export interface TeacherOverview {
  assigned_course_count: number;
  student_count: number;
  new_homework_count: number;
  to_grade_count: number;
  graded_count: number;
  average_progress: number;
}

export interface TeacherStudent {
  id: string;
  name: string;
  email: string;
  course_title: string;
  course_level: string;
  progress: number;
  last_activity: string | null;
}

export interface TeacherHomeworkFilters {
  status?: string;
  course_id?: string;
  level?: string;
  lesson_id?: string;
  search?: string;
}

export interface TeacherLegacyWritingItem {
  id: string;
  student_id: string;
  student_name: string;
  student_email: string;
  course_title: string;
  course_level: string;
  lesson_title: string;
  lesson_number: number;
  writing_title: string;
  min_words: number;
  max_words: number;
  answer_text: string;
  status: "SUBMITTED" | "GRADED" | "NEEDS_REVISION";
  submitted_at: string | null;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
}

export interface TeacherLegacySpeakingItem {
  id: string;
  student_id: string;
  student_name: string;
  student_email: string;
  course_title: string;
  course_level: string;
  lesson_title: string;
  lesson_number: number;
  speaking_title: string;
  duration_seconds: number | null;
  status: "SUBMITTED" | "GRADED" | "NEEDS_REVISION";
  submitted_at: string | null;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
}

// ==========================
// Vorbereitung (Zertifikat/Modelltest) — the real exam-attempt
// submissions (app/models/mock_writing_submission.py, mock_speaking_
// submission.py), never the Assessment Engine's own WritingSubmission/
// SpeakingSubmission (that engine has no consumer in the real exam
// attempt flow — see backend/app/services/mock_exam/teacher_review_
// service.py's module docstring).
// ==========================

export interface TeacherMockWritingSubmission {
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
  ai_evaluated_at: string | null;
  teacher_score: number | null;
  teacher_feedback: string | null;
  submitted_at: string;
}

export interface TeacherMockWritingItem {
  submission: TeacherMockWritingSubmission;
  student_username: string;
  student_email: string;
  provider_name: string;
  level_code: string;
  model_test_title: string;
  teil_title: string;
  task_text: string;
  word_limit: number | null;
}

export interface TeacherMockSpeakingSubmission {
  id: string;
  attempt_id: string;
  speaking_task_id: string;
  audio_url: string;
  transcript: string | null;
  ai_score: number | null;
  ai_feedback: string | null;
  ai_evaluated_at: string | null;
  teacher_score: number | null;
  teacher_feedback: string | null;
  submitted_at: string;
}

export interface TeacherMockSpeakingItem {
  submission: TeacherMockSpeakingSubmission;
  student_username: string;
  student_email: string;
  provider_name: string;
  level_code: string;
  model_test_title: string;
  teil_title: string;
  task_text: string;
}

// ==========================
// VIZU-MOCK Schreiben — unscoped (no course concept), same as
// Vorbereitung above (app/services/teacher/vizu_mock_writing_review_
// service.py). One row per attempt (all 5 Aufgabe graded together).
// ==========================

export interface VizuMockTeacherWritingListItem {
  attempt_id: string;
  student_name: string;
  username: string;
  email: string;
  schreiben_submitted_at: string;
  graded_count: number;
  total_tasks: number;
  schreiben_score: number | null;
  max_score: number;
  status: "NEW" | "IN_PROGRESS" | "GRADED";
}

export interface VizuMockWritingRubricCriterion {
  id: string;
  name: string;
  max_score: number;
  order_index: number;
}

export interface VizuMockTeacherWritingSubmissionDetail {
  task_id: string;
  order_index: number;
  level: string;
  title: string;
  instruction: string;
  min_words: number;
  max_words: number;
  image_url: string | null;
  content: string;
  word_count: number;
  rubric_criteria: VizuMockWritingRubricCriterion[];
  criterion_scores: Record<string, number>;
  teacher_score: number | null;
  teacher_comment: string | null;
}

export interface VizuMockTeacherWritingDetail {
  attempt_id: string;
  student_name: string;
  username: string;
  email: string;
  schreiben_submitted_at: string;
  schreiben_score: number | null;
  schreiben_level: string | null;
  schreiben_feedback: string | null;
  submissions: VizuMockTeacherWritingSubmissionDetail[];
}
