import { api } from "@/services/api";

import type {
  AdminLessonItem,
  AdminModuleOption,
  CreateLessonInput,
  UpdateLessonInput,
} from "../types/lesson";

interface AdminLessonApiPayload {
  id: string;
  module_id: string;
  number: number;
  title: string;
  duration: number;
  video_url: string | null;
  is_free: boolean;
}

interface AdminModuleApiPayload {
  id: string;
  course_id: string;
  title: string;
}

function mapLesson(raw: AdminLessonApiPayload): AdminLessonItem {
  return {
    id: raw.id,
    moduleId: raw.module_id,
    number: raw.number,
    title: raw.title,
    duration: raw.duration,
    isFree: raw.is_free,
    videoUrl: raw.video_url,
  };
}

export async function listLessons(): Promise<AdminLessonItem[]> {
  const response = await api.get("/lessons");
  return response.data.map(mapLesson);
}

export async function getLesson(lessonId: string): Promise<AdminLessonItem> {
  const response = await api.get(`/lessons/${lessonId}`);
  return mapLesson(response.data);
}

export async function createLesson(input: CreateLessonInput): Promise<AdminLessonItem> {
  const response = await api.post("/lessons", {
    module_id: input.moduleId,
    number: input.number,
    title: input.title,
    duration: input.duration,
    is_free: input.isFree ?? false,
    video_url: input.videoUrl || null,
  });
  return mapLesson(response.data);
}

export async function updateLesson(
  lessonId: string,
  data: UpdateLessonInput,
): Promise<AdminLessonItem> {
  const response = await api.put(`/lessons/${lessonId}`, {
    module_id: data.moduleId,
    number: data.number,
    title: data.title,
    duration: data.duration,
    is_free: data.isFree,
    video_url: data.videoUrl,
  });
  return mapLesson(response.data);
}

export async function deleteLesson(lessonId: string): Promise<void> {
  await api.delete(`/lessons/${lessonId}`);
}

export async function listModuleOptions(): Promise<AdminModuleOption[]> {
  const response = await api.get("/modules");
  return response.data.map((raw: AdminModuleApiPayload) => ({
    id: raw.id,
    title: raw.title,
    courseId: raw.course_id,
  }));
}
