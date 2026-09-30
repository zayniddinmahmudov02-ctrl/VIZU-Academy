import { api } from "@/src/services/api";

export interface QuizCsvImportResult {
  quiz_id: string;
  quiz_type: string;
  created_questions: number;
  updated_questions: number;
  total_questions: number;
}

// Admin-only CSV import for the legacy Quiz system (currently used for
// the lesson's Hören quiz) — see backend/app/api/admin/quiz_router.py
// and services/quiz/csv_import_service.py. Idempotent: re-importing the
// same or an edited CSV updates existing questions/options in place.
export async function importQuizCsv(
  lessonId: string,
  quizType: string,
  quizTitle: string,
  file: File,
): Promise<QuizCsvImportResult> {
  const formData = new FormData();
  formData.append("lesson_id", lessonId);
  formData.append("quiz_type", quizType);
  formData.append("quiz_title", quizTitle);
  formData.append("file", file);

  const response = await api.post<QuizCsvImportResult>("/api/v1/admin/quiz/import-csv", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}
