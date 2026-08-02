import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  Quiz,
  QuizCreate,
  QuizOption,
  QuizOptionCreate,
  QuizOptionUpdate,
  QuizQuestion,
  QuizQuestionCreate,
  QuizQuestionUpdate,
  QuizUpdate,
} from "../types/content.types";

export const quizzesApi = createCrudApi<Quiz, QuizCreate, QuizUpdate>(
  ADMIN_ENDPOINTS.quizzes,
);

export const quizQuestionsApi = createCrudApi<
  QuizQuestion,
  QuizQuestionCreate,
  QuizQuestionUpdate
>(ADMIN_ENDPOINTS.quizQuestions);

export const quizOptionsApi = createCrudApi<QuizOption, QuizOptionCreate, QuizOptionUpdate>(
  ADMIN_ENDPOINTS.quizOptions,
);
