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
  PublicAssessment,
  SubmitAnswerInput,
  TaskOption,
  TaskOptionCreate,
  TaskOptionUpdate,
  TaskQuestion,
  TaskQuestionCreate,
  TaskQuestionUpdate,
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
