import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  Exam,
  ExamCreate,
  ExamProvider,
  ExamProviderCreate,
  ExamProviderUpdate,
  ExamUpdate,
} from "../types/content.types";

export const examProvidersApi = createCrudApi<ExamProvider, ExamProviderCreate, ExamProviderUpdate>(
  ADMIN_ENDPOINTS.examProviders,
);

export const examsApi = createCrudApi<Exam, ExamCreate, ExamUpdate>(ADMIN_ENDPOINTS.exams);
