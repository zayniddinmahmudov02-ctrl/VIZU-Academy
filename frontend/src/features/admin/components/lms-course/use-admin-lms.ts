"use client";

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { getAdminLevelLessons, getAdminLevels, getAdminLmsLesson } from "@/features/admin/services/lms-course-service";

export const adminLmsKeys = {
  levels: ["admin-lms", "levels"] as const,
  level: (level: string) => ["admin-lms", "level", level.toUpperCase()] as const,
  lesson: (lessonId: string) => ["admin-lms", "lesson", lessonId] as const,
  progress: (lessonId: string, page: number) => ["admin-lms", "progress", lessonId, page] as const,
  health: (level: string) => ["admin-lms", "health", level] as const,
};

export const useAdminLevels = () => useQuery({ queryKey: adminLmsKeys.levels, queryFn: getAdminLevels });
export const useAdminLevelLessons = (level: string) =>
  useQuery({ queryKey: adminLmsKeys.level(level), queryFn: () => getAdminLevelLessons(level.toUpperCase()) });
export const useAdminLmsLesson = (lessonId: string) =>
  useQuery({ queryKey: adminLmsKeys.lesson(lessonId), queryFn: () => getAdminLmsLesson(lessonId), enabled: !!lessonId });

/** Content changes are allowed (server-side) for these roles only; the UI
 * merely hides controls the server would refuse anyway. */
const EDITOR_ROLES = new Set(["SUPER_ADMIN", "ADMIN", "CONTENT_MANAGER"]);
export function useCanEditCourses(): boolean {
  const { user } = useCurrentUser();
  return !!user && EDITOR_ROLES.has(user.role);
}

// keys the reused content managers (videos, words, rules, Lesen, Hören,
// Schreiben, Sprechen, exercise sets) invalidate after a change
const CONTENT_KEYS = new Set(["admin-lesson-skills", "videos-by-lesson", "speakings", "writings"]);

/** Re-reads the editor's lesson (content counts, videos) whenever one of the
 * reused content managers changed something. */
export function useAdminLmsLessonSync(lessonId: string) {
  const queryClient = useQueryClient();
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (event.type !== "updated" || event.action.type !== "invalidate") return;
      const head = event.query.queryKey[0];
      if (typeof head !== "string" || !CONTENT_KEYS.has(head)) return;
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => queryClient.invalidateQueries({ queryKey: adminLmsKeys.lesson(lessonId) }), 250);
    });
    return () => {
      if (timer) clearTimeout(timer);
      unsubscribe();
    };
  }, [lessonId, queryClient]);
}

export const UNSAVED_MESSAGE = "Es gibt ungespeicherte Änderungen. Trotzdem verlassen?";

/** Warns before leaving with unsaved changes: browser reload / close, and any
 * in-app link click (App Router has no navigation-cancel event). */
export function useUnsavedChangesWarning(dirty: boolean) {
  useEffect(() => {
    if (!dirty) return;
    const beforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    const onClick = (e: MouseEvent) => {
      const anchor = (e.target as HTMLElement | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!anchor || anchor.target === "_blank" || anchor.href.startsWith("blob:")) return;
      if (!window.confirm(UNSAVED_MESSAGE)) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    window.addEventListener("beforeunload", beforeUnload);
    document.addEventListener("click", onClick, true);
    return () => {
      window.removeEventListener("beforeunload", beforeUnload);
      document.removeEventListener("click", onClick, true);
    };
  }, [dirty]);
}
