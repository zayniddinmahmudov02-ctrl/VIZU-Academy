import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  Reading,
  ReadingCreate,
  ReadingOption,
  ReadingOptionCreate,
  ReadingOptionUpdate,
  ReadingQuestion,
  ReadingQuestionCreate,
  ReadingQuestionUpdate,
  ReadingUpdate,
} from "../types/content.types";

export const readingsApi = createCrudApi<Reading, ReadingCreate, ReadingUpdate>(
  ADMIN_ENDPOINTS.readings,
);

export const readingQuestionsApi = createCrudApi<
  ReadingQuestion,
  ReadingQuestionCreate,
  ReadingQuestionUpdate
>(ADMIN_ENDPOINTS.readingQuestions);

export const readingOptionsApi = createCrudApi<
  ReadingOption,
  ReadingOptionCreate,
  ReadingOptionUpdate
>(ADMIN_ENDPOINTS.readingOptions);
