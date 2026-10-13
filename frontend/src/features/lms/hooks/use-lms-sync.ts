"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { lmsKeys } from "./use-lms";

// Keys the existing lesson sections invalidate after a submit / grading
// event (exercise sets, Lesen / Hören tests, Schreiben / Sprechen, video).
const CONTENT_KEYS = new Set(["section-gate", "lesson-skill-results", "lesson-exercises", "writing-submission", "speaking-submission"]);

/** Keeps the LMS lesson state in step with the reused lesson sections: when
 * one of them invalidates its data after the student did something, the
 * lesson is re-read from the server (which recomputes the snapshot). No
 * progress is computed on the client. */
export function useLmsLessonSync(lessonId: string) {
  const queryClient = useQueryClient();

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (event.type !== "updated" || event.action.type !== "invalidate") return;
      const head = event.query.queryKey[0];
      if (typeof head !== "string" || !CONTENT_KEYS.has(head)) return;
      // several keys are invalidated together — refetch once
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: lmsKeys.lesson(lessonId) });
        queryClient.invalidateQueries({ queryKey: ["lms", "level"] });
        queryClient.invalidateQueries({ queryKey: lmsKeys.levels });
      }, 300);
    });
    return () => {
      if (timer) clearTimeout(timer);
      unsubscribe();
    };
  }, [lessonId, queryClient]);
}
