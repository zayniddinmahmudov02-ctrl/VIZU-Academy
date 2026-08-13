import { api } from "@/src/services/api";
import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Lesson, LessonCreate, LessonUpdate } from "../types/content.types";

export const lessonsApi = createCrudApi<Lesson, LessonCreate, LessonUpdate>(
  ADMIN_ENDPOINTS.lessons,
);

export async function getLesson(id: string): Promise<Lesson> {
  const response = await api.get<Lesson>(`${ADMIN_ENDPOINTS.lessons}/${id}`);
  return response.data;
}

export async function getLessonsByModule(moduleId: string): Promise<Lesson[]> {
  const response = await api.get<Lesson[]>(ADMIN_ENDPOINTS.lessonsByModule(moduleId));
  return response.data;
}

export interface LessonContentStatus {
  lesson_id: string;
  number: number;
  title: string;
  has_video: boolean;
  has_grammar: boolean;
  has_vocabulary: boolean;
  has_lesen: boolean;
  has_hoeren: boolean;
  has_schreiben: boolean;
  has_sprechen: boolean;
  /** Position-based (first 3 per level free) — independent of has_* above.
   *  Content can exist and still be locked for a free student. */
  is_locked: boolean;
}

export async function getLessonsContentStatus(moduleId: string): Promise<LessonContentStatus[]> {
  const response = await api.get<LessonContentStatus[]>(ADMIN_ENDPOINTS.lessonsContentStatus(moduleId));
  return response.data;
}
