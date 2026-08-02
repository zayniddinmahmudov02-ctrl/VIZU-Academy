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
