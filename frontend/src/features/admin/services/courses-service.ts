import { api } from "@/services/api";

import type {
  AdminCourseItem,
  CreateCourseInput,
  UpdateCourseInput,
} from "../types/course";

interface AdminCourseApiPayload {
  id: string;
  language_id: string;
  level: string;
  title: string;
  description: string | null;
  order_index: number;
  is_active: boolean;
}

function mapCourse(raw: AdminCourseApiPayload): AdminCourseItem {
  return {
    id: raw.id,
    languageId: raw.language_id,
    level: raw.level,
    title: raw.title,
    description: raw.description,
    orderIndex: raw.order_index,
    isActive: raw.is_active,
  };
}

export async function listCourses(): Promise<AdminCourseItem[]> {
  const response = await api.get("/courses/");
  return response.data.map(mapCourse);
}

export async function createCourse(input: CreateCourseInput): Promise<AdminCourseItem> {
  const response = await api.post("/courses/", {
    language_id: input.languageId,
    level: input.level,
    title: input.title,
    description: input.description || null,
    order_index: input.orderIndex ?? 1,
    is_active: input.isActive ?? true,
  });
  return mapCourse(response.data);
}

export async function updateCourse(
  courseId: string,
  data: UpdateCourseInput,
): Promise<AdminCourseItem> {
  const response = await api.put(`/courses/${courseId}`, {
    language_id: data.languageId,
    level: data.level,
    title: data.title,
    description: data.description,
    order_index: data.orderIndex,
    is_active: data.isActive,
  });
  return mapCourse(response.data);
}

export async function deleteCourse(courseId: string): Promise<void> {
  await api.delete(`/courses/${courseId}`);
}
