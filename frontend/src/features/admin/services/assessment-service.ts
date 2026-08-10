import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  Assessment,
  AssessmentAttempt,
  AssessmentCreate,
  AssessmentResult,
  AssessmentSection,
  AssessmentSectionCreate,
  AssessmentSectionUpdate,
  AssessmentTask,
  AssessmentTaskCreate,
  AssessmentTaskUpdate,
  AssessmentUpdate,
  AudioPlayStatus,
  PendingSpeakingReviewItem,
  PendingWritingReviewItem,
  PublicAssessment,
  SpeakingResult,
  SpeakingReviewInput,
  SpeakingSubmission,
  SubmitAnswerInput,
  TaskAudio,
  TaskOption,
  TaskOptionCreate,
  TaskOptionUpdate,
  TaskQuestion,
  TaskQuestionCreate,
  TaskQuestionUpdate,
  TeacherReviewInput,
  WritingResult,
  WritingRubricCriterion,
  WritingRubricCriterionCreate,
  WritingRubricCriterionUpdate,
  WritingSubmission,
} from "../types/assessment.types";

interface TaskValidation {
  task_id: string;
  is_publishable: boolean;
  errors: string[];
}

// ============================================================
// Admin — Assessments
// ============================================================

export async function listAssessments(params?: {
  assessment_type?: string;
  status?: string;
  lesson_id?: string;
}): Promise<Assessment[]> {
  const response = await api.get<Assessment[]>(ADMIN_ENDPOINTS.assessments, { params });
  return ensureArray<Assessment>(response.data);
}

export async function getAssessment(id: string): Promise<Assessment> {
  const response = await api.get<Assessment>(`${ADMIN_ENDPOINTS.assessments}/${id}`);
  return response.data;
}

export async function createAssessment(data: AssessmentCreate): Promise<Assessment> {
  const response = await api.post<Assessment>(ADMIN_ENDPOINTS.assessments, data);
  return response.data;
}

export async function updateAssessment(id: string, data: AssessmentUpdate): Promise<Assessment> {
  const response = await api.put<Assessment>(`${ADMIN_ENDPOINTS.assessments}/${id}`, data);
  return response.data;
}

export async function deleteAssessment(id: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.assessments}/${id}`);
}

// ============================================================
// Admin — Sections
// ============================================================

export async function listSections(assessmentId: string): Promise<AssessmentSection[]> {
  const response = await api.get<AssessmentSection[]>(`${ADMIN_ENDPOINTS.assessments}/${assessmentId}/sections`);
  return ensureArray<AssessmentSection>(response.data);
}

export async function createSection(
  assessmentId: string,
  data: Omit<AssessmentSectionCreate, "assessment_id">,
): Promise<AssessmentSection> {
  const response = await api.post<AssessmentSection>(`${ADMIN_ENDPOINTS.assessments}/${assessmentId}/sections`, data);
  return response.data;
}

export async function updateSection(id: string, data: AssessmentSectionUpdate): Promise<AssessmentSection> {
  const response = await api.put<AssessmentSection>(`${ADMIN_ENDPOINTS.sections}/${id}`, data);
  return response.data;
}

export async function deleteSection(id: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.sections}/${id}`);
}

// ============================================================
// Admin — Tasks
// ============================================================

export async function listTasks(sectionId: string): Promise<AssessmentTask[]> {
  const response = await api.get<AssessmentTask[]>(`${ADMIN_ENDPOINTS.sections}/${sectionId}/tasks`);
  return ensureArray<AssessmentTask>(response.data);
}

export async function getTask(id: string): Promise<AssessmentTask> {
  const response = await api.get<AssessmentTask>(`${ADMIN_ENDPOINTS.tasks}/${id}`);
  return response.data;
}

export async function createTask(
  sectionId: string,
  data: Omit<AssessmentTaskCreate, "section_id">,
): Promise<AssessmentTask> {
  const response = await api.post<AssessmentTask>(`${ADMIN_ENDPOINTS.sections}/${sectionId}/tasks`, data);
  return response.data;
}

export async function updateTask(id: string, data: AssessmentTaskUpdate): Promise<AssessmentTask> {
  const response = await api.put<AssessmentTask>(`${ADMIN_ENDPOINTS.tasks}/${id}`, data);
  return response.data;
}

export async function deleteTask(id: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.tasks}/${id}`);
}

export async function validateTask(id: string): Promise<TaskValidation> {
  const response = await api.get<TaskValidation>(`${ADMIN_ENDPOINTS.tasks}/${id}/validate`);
  return response.data;
}

// ============================================================
// Admin — Questions
// ============================================================

export async function createQuestion(
  taskId: string,
  data: Omit<TaskQuestionCreate, "task_id">,
): Promise<TaskQuestion> {
  const response = await api.post<TaskQuestion>(`${ADMIN_ENDPOINTS.tasks}/${taskId}/questions`, data);
  return response.data;
}

export async function updateQuestion(id: string, data: TaskQuestionUpdate): Promise<TaskQuestion> {
  const response = await api.put<TaskQuestion>(`${ADMIN_ENDPOINTS.questions}/${id}`, data);
  return response.data;
}

export async function deleteQuestion(id: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.questions}/${id}`);
}

// ============================================================
// Admin — Options
// ============================================================

export async function createOption(
  questionId: string,
  data: Omit<TaskOptionCreate, "question_id">,
): Promise<TaskOption> {
  const response = await api.post<TaskOption>(`${ADMIN_ENDPOINTS.questions}/${questionId}/options`, data);
  return response.data;
}

export async function updateOption(id: string, data: TaskOptionUpdate): Promise<TaskOption> {
  const response = await api.put<TaskOption>(`${ADMIN_ENDPOINTS.options}/${id}`, data);
  return response.data;
}

export async function deleteOption(id: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.options}/${id}`);
}

// ============================================================
// Public / student-facing
// ============================================================

export async function getPublicLessonAssessment(lessonId: string): Promise<PublicAssessment | null> {
  const response = await api.get<PublicAssessment | null>(
    `${ADMIN_ENDPOINTS.publicLessonAssessment}/${lessonId}/assessment`,
  );
  return response.data;
}

export async function getPublicAssessment(assessmentId: string): Promise<PublicAssessment> {
  const response = await api.get<PublicAssessment>(`${ADMIN_ENDPOINTS.publicAssessment}/${assessmentId}`);
  return response.data;
}

export async function startAttempt(assessmentId: string): Promise<AssessmentAttempt> {
  const response = await api.post<AssessmentAttempt>(ADMIN_ENDPOINTS.attempts, { assessment_id: assessmentId });
  return response.data;
}

export async function submitAnswer(attemptId: string, data: SubmitAnswerInput) {
  const response = await api.post(`${ADMIN_ENDPOINTS.attempts}/${attemptId}/answers`, data);
  return response.data;
}

export async function submitAttempt(attemptId: string): Promise<AssessmentAttempt> {
  const response = await api.post<AssessmentAttempt>(`${ADMIN_ENDPOINTS.attempts}/${attemptId}/submit`);
  return response.data;
}

export async function getAttemptResult(attemptId: string): Promise<AssessmentResult> {
  const response = await api.get<AssessmentResult>(`${ADMIN_ENDPOINTS.attempts}/${attemptId}/result`);
  return response.data;
}

// ============================================================
// Audio (HOEREN)
// ============================================================

export async function uploadTaskAudio(
  taskId: string,
  file: File,
  durationSeconds?: number,
): Promise<TaskAudio> {
  const formData = new FormData();
  formData.append("file", file);
  if (durationSeconds != null) formData.append("duration_seconds", String(Math.round(durationSeconds)));

  const response = await api.post<TaskAudio>(`${ADMIN_ENDPOINTS.tasks}/${taskId}/audio`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function deleteTaskAudio(taskId: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.tasks}/${taskId}/audio`);
}

// Audio is never a static URL — GET /audio/{task_id} re-checks permission
// on every request, so the frontend fetches it through the authenticated
// client and turns the response into a local blob URL for the <audio>
// element (same pattern as certificate downloads).
export async function getAudioBlobUrl(taskId: string): Promise<string> {
  const response = await api.get(`${ADMIN_ENDPOINTS.audio}/${taskId}`, { responseType: "blob" });
  return URL.createObjectURL(response.data as Blob);
}

export async function getAudioStatus(taskId: string): Promise<AudioPlayStatus> {
  const response = await api.get<AudioPlayStatus>(`${ADMIN_ENDPOINTS.tasks}/${taskId}/audio-status`);
  return response.data;
}

export async function registerAudioPlay(taskId: string): Promise<AudioPlayStatus> {
  const response = await api.post<AudioPlayStatus>(`${ADMIN_ENDPOINTS.tasks}/${taskId}/audio-play`);
  return response.data;
}

// Generic backend file upload (POST /upload/{folder}) — reused as-is for
// the writing task's prompt image rather than building a dedicated
// endpoint; the same route already serves videos/thumbnails/audio/etc.
export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<{ url: string }>(`${ADMIN_ENDPOINTS.upload}/images`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data.url;
}

// ============================================================
// Writing rubric criteria (SCHREIBEN) — admin builder
// ============================================================

export async function createRubricCriterion(
  taskId: string,
  data: WritingRubricCriterionCreate,
): Promise<WritingRubricCriterion> {
  const response = await api.post<WritingRubricCriterion>(`${ADMIN_ENDPOINTS.tasks}/${taskId}/rubric-criteria`, data);
  return response.data;
}

export async function updateRubricCriterion(
  id: string,
  data: WritingRubricCriterionUpdate,
): Promise<WritingRubricCriterion> {
  const response = await api.put<WritingRubricCriterion>(`${ADMIN_ENDPOINTS.rubricCriteria}/${id}`, data);
  return response.data;
}

export async function deleteRubricCriterion(id: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.rubricCriteria}/${id}`);
}

// ============================================================
// Writing submissions — Speichern / Abgeben / results (student-facing)
// ============================================================

export async function getWritingSubmission(attemptId: string, taskId: string): Promise<WritingSubmission | null> {
  const response = await api.get<WritingSubmission | null>(`${ADMIN_ENDPOINTS.attempts}/${attemptId}/writing/${taskId}`);
  return response.data;
}

export async function saveWritingDraft(attemptId: string, taskId: string, content: string): Promise<WritingSubmission> {
  const response = await api.put<WritingSubmission>(`${ADMIN_ENDPOINTS.attempts}/${attemptId}/writing/${taskId}`, {
    content,
  });
  return response.data;
}

export async function submitWriting(attemptId: string, taskId: string): Promise<WritingSubmission> {
  const response = await api.post<WritingSubmission>(
    `${ADMIN_ENDPOINTS.attempts}/${attemptId}/writing/${taskId}/submit`,
  );
  return response.data;
}

export async function getWritingResult(attemptId: string, taskId: string): Promise<WritingResult> {
  const response = await api.get<WritingResult>(`${ADMIN_ENDPOINTS.attempts}/${attemptId}/writing/${taskId}/result`);
  return response.data;
}

// ============================================================
// Teacher review — AI_AND_TEACHER / TEACHER_ONLY
// ============================================================

export async function listPendingWritingReviews(assessmentId?: string): Promise<PendingWritingReviewItem[]> {
  const response = await api.get<PendingWritingReviewItem[]>(`${ADMIN_ENDPOINTS.writing}/pending-review`, {
    params: assessmentId ? { assessment_id: assessmentId } : undefined,
  });
  return ensureArray<PendingWritingReviewItem>(response.data);
}

export async function reviewWritingSubmission(submissionId: string, data: TeacherReviewInput) {
  const response = await api.post(`${ADMIN_ENDPOINTS.writing}/${submissionId}/review`, data);
  return response.data;
}

// ============================================================
// Speaking submissions — Aufnahme upload/re-record, results (student-facing)
// ============================================================

export async function getSpeakingSubmission(attemptId: string, taskId: string): Promise<SpeakingSubmission | null> {
  const response = await api.get<SpeakingSubmission | null>(
    `${ADMIN_ENDPOINTS.attempts}/${attemptId}/speaking/${taskId}`,
  );
  return response.data;
}

export async function uploadSpeakingSubmission(
  attemptId: string,
  taskId: string,
  file: Blob,
  durationSeconds: number,
  extension: string,
): Promise<SpeakingSubmission> {
  const formData = new FormData();
  formData.append("file", file, `recording.${extension}`);
  formData.append("duration_seconds", String(Math.round(durationSeconds)));
  const response = await api.post<SpeakingSubmission>(
    `${ADMIN_ENDPOINTS.attempts}/${attemptId}/speaking/${taskId}`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

// Same never-a-public-URL pattern as getAudioBlobUrl — permission is
// re-checked on every request server-side.
export async function getSpeakingAudioBlobUrl(submissionId: string): Promise<string> {
  const response = await api.get(`${ADMIN_ENDPOINTS.speakingSubmissions}/${submissionId}/audio`, {
    responseType: "blob",
  });
  return URL.createObjectURL(response.data as Blob);
}

export async function getSpeakingResult(attemptId: string, taskId: string): Promise<SpeakingResult> {
  const response = await api.get<SpeakingResult>(`${ADMIN_ENDPOINTS.attempts}/${attemptId}/speaking/${taskId}/result`);
  return response.data;
}

// ============================================================
// Teacher review — Sprechen
// ============================================================

export async function listPendingSpeakingReviews(assessmentId?: string): Promise<PendingSpeakingReviewItem[]> {
  const response = await api.get<PendingSpeakingReviewItem[]>(`${ADMIN_ENDPOINTS.speaking}/pending-review`, {
    params: assessmentId ? { assessment_id: assessmentId } : undefined,
  });
  return ensureArray<PendingSpeakingReviewItem>(response.data);
}

export async function reviewSpeakingSubmission(submissionId: string, data: SpeakingReviewInput) {
  const response = await api.post(`${ADMIN_ENDPOINTS.speaking}/${submissionId}/review`, data);
  return response.data;
}
