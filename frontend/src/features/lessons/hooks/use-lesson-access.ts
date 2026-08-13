"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { getLesson } from "../services/lesson-service";

export type LessonAccessState = "loading" | "granted" | "premium_required" | "error";

/** GET /lessons/{id} is the same endpoint the backend gates behind
 *  can_access_lesson (first-3-per-level free, Premium/staff otherwise) —
 *  reusing it here means this hook can never drift from what the server
 *  actually enforces. A non-403 failure is reported as "error" rather
 *  than silently granting or blocking access. */
export function useLessonAccess(lessonId: string): LessonAccessState {
  const [state, setState] = useState<LessonAccessState>("loading");

  useEffect(() => {
    if (!lessonId) {
      setState("error");
      return;
    }

    let isMounted = true;
    setState("loading");

    getLesson(lessonId)
      .then(() => {
        if (isMounted) setState("granted");
      })
      .catch((err) => {
        if (!isMounted) return;
        setState(err instanceof ApiError && err.status === 403 ? "premium_required" : "error");
      });

    return () => {
      isMounted = false;
    };
  }, [lessonId]);

  return state;
}
