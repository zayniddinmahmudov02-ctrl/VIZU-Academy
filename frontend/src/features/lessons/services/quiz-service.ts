import { api } from "@/lib/api";

export type QuizType = "GRAMMAR" | "LESSON" | "VOCABULARY";

export interface LessonQuiz {
  id: string;
  lesson_id: string;
  quiz_type: QuizType;
  title: string;
  description: string | null;
  passing_score: number;
  order_index: number;
  is_published: boolean;
}

export type QuizQuestionType =
  | "MULTIPLE_CHOICE"
  | "TRUE_FALSE"
  | "CLOZE_TEXT"
  | "SENTENCE_COMPLETION"
  | "SENTENCE_ORDERING"
  | "ERROR_FINDING"
  | "MATCHING";

// Student-facing shape — the backend deliberately omits correct_text_answer
// (question) and is_correct/match_value (option) from these unauthenticated
// reads. Grading happens server-side via submitQuizAttempt(); the correct
// answer is never sent to the client before submission (see
// app/services/quiz/grading_service.py).
export interface LessonQuizQuestion {
  id: string;
  quiz_id: string;
  question: string;
  question_type: QuizQuestionType;
  explanation: string | null;
  points: number;
  order_index: number;
  is_published: boolean;
  // MATCHING only — a fresh, server-shuffled list of just the values (no
  // option_id attached), since each option's own match_value is hidden.
  match_value_pool: string[] | null;
}

export interface LessonQuizOption {
  id: string;
  question_id: string;
  option_text: string;
  order_index: number;
}

// Public — no video/lesson-access gate of its own beyond what the lesson
// page itself already enforces; the underlying quiz/question/option GETs
// are unauthenticated reads, same as the rest of this legacy quiz system.
export async function getLessonQuizzes(lessonId: string, quizType: QuizType): Promise<LessonQuiz[]> {
  return api<LessonQuiz[]>(
    `/api/v1/quizzes/lesson/${lessonId}?quiz_type=${quizType}&published_only=true`,
  );
}

// No per-quiz filter exists server-side (legacy system) — fetch everything
// and filter client-side, same pattern the admin question editor already uses.
export async function getQuizQuestions(quizId: string): Promise<LessonQuizQuestion[]> {
  const all = await api<LessonQuizQuestion[]>(`/api/v1/quiz-questions`);
  return all
    .filter((q) => q.quiz_id === quizId && q.is_published)
    .sort((a, b) => a.order_index - b.order_index);
}

export async function getQuizOptions(questionId: string): Promise<LessonQuizOption[]> {
  const all = await api<LessonQuizOption[]>(`/api/v1/quiz-options`);
  return all
    .filter((o) => o.question_id === questionId)
    .sort((a, b) => a.order_index - b.order_index);
}

// ============================================================
// Server-side grading — POST /quizzes/{quizId}/submit
// ============================================================

export interface QuizAnswerSubmit {
  question_id: string;
  option_id?: string | null;
  text_answer?: string | null;
  ordered_option_ids?: string[] | null;
  matches?: Record<string, string> | null;
}

export interface QuizAnswerResult {
  question_id: string;
  is_correct: boolean;
  correct_option_id: string | null;
  correct_text_answer: string | null;
  correct_order_option_ids: string[] | null;
  correct_matches: Record<string, string> | null;
}

export interface QuizSubmitResult {
  score: number;
  correct_answers: number;
  wrong_answers: number;
  skipped_answers: number;
  passed: boolean;
  results: QuizAnswerResult[];
}

export async function submitQuizAttempt(
  quizId: string,
  answers: QuizAnswerSubmit[],
): Promise<QuizSubmitResult> {
  return api<QuizSubmitResult>(`/api/v1/quizzes/${quizId}/submit`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}
