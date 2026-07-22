"use client";

import { useEffect, useState } from "react";

import type { Lesson } from "../types/lesson";
import { getLesson } from "../services/lesson-service";

interface UseLessonResult {
  lesson: Lesson | null;
  loading: boolean;
  /** A translation key (resolve with `t()`), not display text. */
  error: string | null;
}

export function useLesson(
  lessonId: string,
): UseLessonResult {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!lessonId) {
      setLoading(false);
      setError("lessons.loadLessonError");
      return;
    }

    let isMounted = true;

    async function fetchLesson() {
      try {
        setLoading(true);
        setError(null);

        const data = await getLesson(lessonId);

        if (isMounted) {
          setLesson(data);
        }
      } catch (err) {
        console.warn("Failed to load lesson:", err);

        if (isMounted) {
          setLesson(null);
          setError("lessons.loadLessonError");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchLesson();

    return () => {
      isMounted = false;
    };
  }, [lessonId]);

  return {
    lesson,
    loading,
    error,
  };
}