import { api } from "@/lib/api";

import type { CompetencyKind, LmsLesson, LmsLevel, LmsLevels, LmsVisitResult } from "../types";

/** VIZU LMS student API (backend: app/api/lms/router.py). Lesson content
 * itself keeps coming from the existing lesson-skills / videos / vocabulary
 * / grammar / writing / speaking services. */

export function getLmsLevels(): Promise<LmsLevels> {
  return api<LmsLevels>("/api/v1/lms/levels");
}

export function getLmsLevel(level: string): Promise<LmsLevel> {
  return api<LmsLevel>(`/api/v1/lms/levels/${encodeURIComponent(level)}`);
}

export function getLmsLesson(lessonId: string): Promise<LmsLesson> {
  return api<LmsLesson>(`/api/v1/lms/lessons/${lessonId}`);
}

export function visitCompetency(lessonId: string, kind: CompetencyKind): Promise<LmsVisitResult> {
  return api<LmsVisitResult>(`/api/v1/lms/lessons/${lessonId}/competencies/${kind}/visit`, { method: "POST" });
}
