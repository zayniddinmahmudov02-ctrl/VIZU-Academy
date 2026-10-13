"use client";

import { useQuery } from "@tanstack/react-query";

import { retryUnlessClientError } from "../errors";
import { getLmsLesson, getLmsLevel, getLmsLevels } from "../services/lms-service";

export const lmsKeys = {
  levels: ["lms", "levels"] as const,
  level: (level: string) => ["lms", "level", level.toUpperCase()] as const,
  lesson: (lessonId: string) => ["lms", "lesson", lessonId] as const,
};

export function useLmsLevels() {
  return useQuery({ queryKey: lmsKeys.levels, queryFn: getLmsLevels, retry: retryUnlessClientError, staleTime: 30_000 });
}

export function useLmsLevel(level: string) {
  return useQuery({ queryKey: lmsKeys.level(level), queryFn: () => getLmsLevel(level), retry: retryUnlessClientError, staleTime: 30_000 });
}

/** The lesson state — the backend recomputes and persists the student's
 * snapshot on every fetch, so this is always the server's truth. */
export function useLmsLesson(lessonId: string) {
  return useQuery({
    queryKey: lmsKeys.lesson(lessonId),
    queryFn: () => getLmsLesson(lessonId),
    retry: retryUnlessClientError,
    staleTime: 15_000,
    enabled: !!lessonId,
  });
}
