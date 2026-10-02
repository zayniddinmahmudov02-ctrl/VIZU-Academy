import { api } from "@/src/services/api";

import type {
  TeacherHomeworkFilters,
  TeacherLegacySpeakingItem,
  TeacherLegacyWritingItem,
  TeacherMockSpeakingItem,
  TeacherMockWritingItem,
  TeacherOverview,
  TeacherStudent,
  VizuMultilevelTeacherWritingDetail,
  VizuMultilevelTeacherWritingListItem,
  VizuMultilevelTeacherSpeakingDetail,
  VizuMultilevelTeacherSpeakingListItem,
} from "../types";

// /api/v1/teacher/* — gated server-side by require_teacher_panel_access
// (TEACHER or SUPER_ADMIN only, see backend/app/api/dependencies/auth.py).
// Scoped to whatever courses the CURRENT caller has a TeacherAssignment
// row for (backend/app/services/teacher/service.py) — never every
// student in the system.
export async function getTeacherOverview(): Promise<TeacherOverview> {
  const response = await api.get<TeacherOverview>("/api/v1/teacher/overview");
  return response.data;
}

export async function getTeacherStudents(): Promise<TeacherStudent[]> {
  const response = await api.get<TeacherStudent[]>("/api/v1/teacher/students");
  return response.data;
}

// ==========================
// Schreiben (legacy Writing) — see app/models/student_writing.py
// ==========================

export async function getTeacherLegacyWritingSubmissions(
  filters: TeacherHomeworkFilters = {},
): Promise<TeacherLegacyWritingItem[]> {
  const response = await api.get<TeacherLegacyWritingItem[]>("/api/v1/teacher/writing", { params: filters });
  return response.data;
}

export async function gradeTeacherLegacyWritingSubmission(
  id: string,
  data: { score: number; feedback: string; status: "GRADED" | "NEEDS_REVISION" },
): Promise<TeacherLegacyWritingItem> {
  const response = await api.patch<TeacherLegacyWritingItem>(`/api/v1/teacher/writing/${id}/grade`, data);
  return response.data;
}

// ==========================
// Sprechen (legacy Speaking) — see app/models/student_speaking.py
// ==========================

export async function getTeacherLegacySpeakingSubmissions(
  filters: TeacherHomeworkFilters = {},
): Promise<TeacherLegacySpeakingItem[]> {
  const response = await api.get<TeacherLegacySpeakingItem[]>("/api/v1/teacher/speaking", { params: filters });
  return response.data;
}

export async function gradeTeacherLegacySpeakingSubmission(
  id: string,
  data: { score: number; feedback: string; status: "GRADED" | "NEEDS_REVISION" },
): Promise<TeacherLegacySpeakingItem> {
  const response = await api.patch<TeacherLegacySpeakingItem>(`/api/v1/teacher/speaking/${id}/grade`, data);
  return response.data;
}

// Same secure-audio pattern as the Assessment Engine's own
// getSpeakingAudioBlobUrl (features/admin/services/assessment-service.ts)
// — never a public URL, permission re-checked server-side on every call.
export async function getTeacherLegacySpeakingAudioBlobUrl(submissionId: string): Promise<string> {
  const response = await api.get(`/api/v1/speakings/submissions/${submissionId}/audio`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

// ==========================
// Vorbereitung (Zertifikat/Modelltest) Schreiben/Sprechen — real exam-
// attempt submissions, grouped by Provider/Level/Modelltest breadcrumb
// on the frontend (see teacher-schreiben/sprechen page components).
// ==========================

export async function getTeacherVorbereitungWriting(): Promise<TeacherMockWritingItem[]> {
  const response = await api.get<TeacherMockWritingItem[]>("/api/v1/teacher/vorbereitung/writing");
  return response.data;
}

export async function aiEvaluateVorbereitungWriting(submissionId: string): Promise<TeacherMockWritingItem> {
  const response = await api.post<TeacherMockWritingItem>(
    `/api/v1/teacher/vorbereitung/writing/${submissionId}/ai-evaluate`,
  );
  return response.data;
}

export async function reviewVorbereitungWriting(
  submissionId: string,
  data: { teacher_score: number | null; teacher_feedback: string | null },
): Promise<TeacherMockWritingItem> {
  const response = await api.put<TeacherMockWritingItem>(
    `/api/v1/teacher/vorbereitung/writing/${submissionId}/review`,
    data,
  );
  return response.data;
}

export async function getTeacherVorbereitungSpeaking(): Promise<TeacherMockSpeakingItem[]> {
  const response = await api.get<TeacherMockSpeakingItem[]>("/api/v1/teacher/vorbereitung/speaking");
  return response.data;
}

export async function aiEvaluateVorbereitungSpeaking(submissionId: string): Promise<TeacherMockSpeakingItem> {
  const response = await api.post<TeacherMockSpeakingItem>(
    `/api/v1/teacher/vorbereitung/speaking/${submissionId}/ai-evaluate`,
  );
  return response.data;
}

export async function reviewVorbereitungSpeaking(
  submissionId: string,
  data: { teacher_score: number | null; teacher_feedback: string | null },
): Promise<TeacherMockSpeakingItem> {
  const response = await api.put<TeacherMockSpeakingItem>(
    `/api/v1/teacher/vorbereitung/speaking/${submissionId}/review`,
    data,
  );
  return response.data;
}

// ==========================
// VIZU-Multilevel Schreiben — see app/services/teacher/
// vizu_multilevel_writing_review_service.py
// ==========================

export async function getTeacherVizuMultilevelWriting(): Promise<VizuMultilevelTeacherWritingListItem[]> {
  const response = await api.get<VizuMultilevelTeacherWritingListItem[]>("/api/v1/teacher/vizu-multilevel/schreiben");
  return response.data;
}

export async function getTeacherVizuMultilevelWritingDetail(attemptId: string): Promise<VizuMultilevelTeacherWritingDetail> {
  const response = await api.get<VizuMultilevelTeacherWritingDetail>(`/api/v1/teacher/vizu-multilevel/schreiben/${attemptId}`);
  return response.data;
}

export async function gradeTeacherVizuMultilevelWritingTask(
  attemptId: string,
  taskId: string,
  data: { criterion_scores: Record<string, number>; comment: string | null },
): Promise<VizuMultilevelTeacherWritingDetail> {
  const response = await api.put<VizuMultilevelTeacherWritingDetail>(
    `/api/v1/teacher/vizu-multilevel/schreiben/${attemptId}/task/${taskId}`,
    data,
  );
  return response.data;
}

export async function setTeacherVizuMultilevelWritingFeedback(
  attemptId: string,
  schreibenFeedback: string | null,
): Promise<VizuMultilevelTeacherWritingDetail> {
  const response = await api.put<VizuMultilevelTeacherWritingDetail>(`/api/v1/teacher/vizu-multilevel/schreiben/${attemptId}/feedback`, {
    schreiben_feedback: schreibenFeedback,
  });
  return response.data;
}

// ==========================
// VIZU-Multilevel Sprechen — see app/services/teacher/
// vizu_multilevel_speaking_review_service.py
// ==========================

export async function getTeacherVizuMultilevelSpeaking(): Promise<VizuMultilevelTeacherSpeakingListItem[]> {
  const response = await api.get<VizuMultilevelTeacherSpeakingListItem[]>("/api/v1/teacher/vizu-multilevel/sprechen");
  return response.data;
}

export async function getTeacherVizuMultilevelSpeakingDetail(attemptId: string): Promise<VizuMultilevelTeacherSpeakingDetail> {
  const response = await api.get<VizuMultilevelTeacherSpeakingDetail>(`/api/v1/teacher/vizu-multilevel/sprechen/${attemptId}`);
  return response.data;
}

// Authenticated fetch -> blob URL (same pattern as the other speaking
// audio helpers above) — never a public URL.
export async function getTeacherVizuMultilevelSpeakingAudioBlobUrl(attemptId: string, submissionId: string): Promise<string> {
  const response = await api.get(`/api/v1/teacher/vizu-multilevel/sprechen/${attemptId}/submissions/${submissionId}/audio`, {
    responseType: "blob",
  });
  return URL.createObjectURL(response.data as Blob);
}

export async function gradeTeacherVizuMultilevelSpeakingTask(
  attemptId: string,
  taskId: string,
  data: { score: number; comment: string | null },
): Promise<VizuMultilevelTeacherSpeakingDetail> {
  const response = await api.put<VizuMultilevelTeacherSpeakingDetail>(
    `/api/v1/teacher/vizu-multilevel/sprechen/${attemptId}/task/${taskId}`,
    data,
  );
  return response.data;
}
