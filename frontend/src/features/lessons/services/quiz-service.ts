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

export interface LessonQuizQuestion {
  id: string;
  quiz_id: string;
  question: string;
  question_type: QuizQuestionType;
  correct_text_answer: string | null;
  explanation: string | null;
  points: number;
  order_index: number;
  is_published: boolean;
}

export interface LessonQuizOption {
  id: string;
  question_id: string;
  option_text: string;
  is_correct: boolean;
  order_index: number;
  match_value: string | null;
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

export interface SubmitQuizResultPayload {
  user_id: string;
  quiz_id: string;
  correct_answers: number;
  wrong_answers: number;
  skipped_answers: number;
  score: number;
  passed: boolean;
}

export async function submitQuizResult(payload: SubmitQuizResultPayload): Promise<void> {
  await api(`/api/v1/student-quizzes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
