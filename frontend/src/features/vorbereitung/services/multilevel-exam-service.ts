import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

import type {
  AdminAttemptDetail,
  AdminAttemptRow,
  AnswerKeyTable,
  AttemptSummary,
  AttemptView,
  ExamListItem,
  ExamPreview,
  ExamResult,
  ExamSection,
  ExamStatistics,
  KeyImportResult,
  KeySection,
  ScoringSettings,
  ScoringSettingsUpdate,
  SectionPaper,
} from "../types/multilevel-exam.types";

// Multilevel exam mode (backend app/api/mock_exam/multilevel_exam_router.py). Scores are computed by the server only.
const BASE = "/api/v1/multilevel-exam";
const ADMIN = "/api/v1/admin/multilevel-exam";

export async function getExams(): Promise<ExamListItem[]> {
  return ensureArray<ExamListItem>((await api.get(`${BASE}/exams`)).data);
}

export async function getHistory(): Promise<AttemptSummary[]> {
  return ensureArray<AttemptSummary>((await api.get(`${BASE}/history`)).data);
}

export async function startAttempt(modelTestId: string): Promise<AttemptView> {
  return (await api.post<AttemptView>(`${BASE}/attempts`, { model_test_id: modelTestId })).data;
}

export async function getAttempt(attemptId: string): Promise<AttemptView> {
  return (await api.get<AttemptView>(`${BASE}/attempts/${attemptId}`)).data;
}

export async function startSection(attemptId: string, section: ExamSection): Promise<SectionPaper> {
  return (await api.post<SectionPaper>(`${BASE}/attempts/${attemptId}/sections/${section}/start`)).data;
}

export async function getSection(attemptId: string, section: ExamSection): Promise<SectionPaper> {
  return (await api.get<SectionPaper>(`${BASE}/attempts/${attemptId}/sections/${section}`)).data;
}

export async function saveAnswer(attemptId: string, section: ExamSection, questionId: string, optionIds: string[]) {
  return (await api.put(`${BASE}/attempts/${attemptId}/sections/${section}/answers`, { question_id: questionId, option_ids: optionIds })).data;
}

export async function saveWriting(attemptId: string, writingTaskId: string, answerText: string) {
  return (await api.put(`${BASE}/attempts/${attemptId}/writing/${writingTaskId}`, { answer_text: answerText })).data;
}

export async function uploadRecording(attemptId: string, speakingTaskId: string, blob: Blob) {
  const form = new FormData();
  const ext = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "m4a" : "webm";
  form.append("file", blob, `recording.${ext}`);
  return (await api.post(`${BASE}/attempts/${attemptId}/speaking/${speakingTaskId}`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  })).data;
}

export async function submitSection(attemptId: string, section: ExamSection) {
  return (await api.post(`${BASE}/attempts/${attemptId}/sections/${section}/submit`)).data;
}

export async function finishAttempt(attemptId: string) {
  return (await api.post(`${BASE}/attempts/${attemptId}/finish`)).data;
}

export async function getResult(attemptId: string): Promise<ExamResult> {
  return (await api.get<ExamResult>(`${BASE}/attempts/${attemptId}/results`)).data;
}

// ── staff ──
export async function getAdminAttempts(params: { model_test_id?: string; status?: string } = {}): Promise<AdminAttemptRow[]> {
  return ensureArray<AdminAttemptRow>((await api.get(`${ADMIN}/attempts`, { params })).data);
}

export async function getAdminAttempt(attemptId: string): Promise<AdminAttemptDetail> {
  return (await api.get<AdminAttemptDetail>(`${ADMIN}/attempts/${attemptId}`)).data;
}

/** Super Admin override of a section score (any of the four); `score` null clears it. The reason is required and kept in the history. */
export async function gradeSection(attemptId: string, section: ExamSection, score: number | null, reason: string, feedback: string | null = null) {
  return (await api.put<AdminAttemptDetail>(`${ADMIN}/attempts/${attemptId}/sections/${section}/grade`, { score, reason, feedback })).data;
}

/** Super Admin: run the AI again (Schreiben / Sprechen); an override stays in force. */
export async function reevaluateSection(attemptId: string, section: ExamSection) {
  return (await api.post<AdminAttemptDetail>(`${ADMIN}/attempts/${attemptId}/sections/${section}/reevaluate`)).data;
}

export async function getStaffRecording(submissionId: string): Promise<Blob> {
  return (await api.get<Blob>(`${ADMIN}/recordings/${submissionId}`, { responseType: "blob" })).data;
}

export async function getStatistics(): Promise<ExamStatistics> {
  return (await api.get<ExamStatistics>(`${ADMIN}/statistics`)).data;
}

export async function getScoringSettings(): Promise<ScoringSettings> {
  return (await api.get<ScoringSettings>(`${ADMIN}/settings`)).data;
}

export async function putScoringSettings(data: ScoringSettingsUpdate): Promise<ScoringSettings> {
  return (await api.put<ScoringSettings>(`${ADMIN}/settings`, data)).data;
}

// ── answer keys (Lesen / Hören): numbered table, save, import check ──
export async function getAnswerKeys(modelTestId: string, section: KeySection): Promise<AnswerKeyTable> {
  return (await api.get<AnswerKeyTable>(`${ADMIN}/model-tests/${modelTestId}/answer-keys`, { params: { section } })).data;
}

export async function putAnswerKeys(modelTestId: string, section: KeySection, answers: Record<string, string>, requireComplete = false): Promise<AnswerKeyTable> {
  return (await api.put<AnswerKeyTable>(`${ADMIN}/model-tests/${modelTestId}/answer-keys`, { section, answers, require_complete: requireComplete })).data;
}

/** dryRun: check the pasted list (count, letters per question type) without saving; otherwise a fully valid list is saved */
export async function importAnswerKeys(modelTestId: string, section: KeySection, text: string, dryRun: boolean): Promise<KeyImportResult> {
  return (await api.post<KeyImportResult>(`${ADMIN}/model-tests/${modelTestId}/answer-keys/import`, { section, text, dry_run: dryRun })).data;
}

export async function getExamPreview(modelTestId: string): Promise<ExamPreview> {
  return (await api.get<ExamPreview>(`${ADMIN}/model-tests/${modelTestId}/preview`)).data;
}
