import { api } from "@/lib/api";

import type { Lesson } from "../types/lesson";

interface LessonListItemPayload {
  id: string;
  module_id: string;
  number: number;
  title: string;
  duration: number;
  video_url: string | null;
  is_free: boolean;
  progress: number;
}

interface LessonDetailPayload extends LessonListItemPayload {
  audio_url: string | null;
}

function mapLessonListItem(payload: LessonListItemPayload): Lesson {
  return {
    id: payload.id,
    moduleId: payload.module_id,
    number: payload.number,
    title: payload.title,
    duration: payload.duration,
    videoUrl: payload.video_url,
    isFree: payload.is_free,
    progress: payload.progress,
  };
}

function mapLessonDetail(payload: LessonDetailPayload): Lesson {
  return {
    ...mapLessonListItem(payload),
    audioUrl: payload.audio_url,
  };
}

// Shape of GET /lessons/module/{module_id} — backend's plain LessonResponse,
// not the progress-aware LessonListItem (that endpoint requires no login,
// so it can't resolve a per-user progress value).
interface LessonByModulePayload {
  id: string;
  module_id: string;
  number: number;
  title: string;
  duration: number;
  video_url: string | null;
  is_free: boolean;
}

function mapLessonByModule(payload: LessonByModulePayload): Lesson {
  return {
    id: payload.id,
    moduleId: payload.module_id,
    number: payload.number,
    title: payload.title,
    duration: payload.duration,
    videoUrl: payload.video_url,
    isFree: payload.is_free,
    progress: 0,
  };
}

// /api/v1/lessons, not bare /lessons — that path is also the Next.js lesson
// player route (/lessons/[lessonId]/[section]), and the production nginx
// gateway reserves it for the frontend. See backend/app/main.py's
// lessons_router mount.

export async function getLesson(
  lessonId: string,
): Promise<Lesson> {
  const payload = await api<LessonDetailPayload>(
    `/api/v1/lessons/${lessonId}`,
  );

  return mapLessonDetail(payload);
}

export async function getLessons() {
  const payload = await api<LessonListItemPayload[]>(
    "/api/v1/lessons",
  );

  return payload.map(mapLessonListItem);
}

// Public — no auth required, matches GET /modules and GET /courses.
// Returns lessons for one module (a level's single wrapping module),
// ordered by number — the real source of truth ModuleList and
// course-hero/course-progress now read from instead of the hardcoded
// COURSE_CONTENT constant.
export async function getLessonsByModule(moduleId: string): Promise<Lesson[]> {
  const payload = await api<LessonByModulePayload[]>(
    `/api/v1/lessons/module/${moduleId}`,
  );

  return payload.map(mapLessonByModule);
}
