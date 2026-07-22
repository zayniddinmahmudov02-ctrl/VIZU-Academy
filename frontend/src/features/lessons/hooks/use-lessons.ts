"use client";

import { useEffect, useState } from "react";

import { getLessons } from "../services/lesson-service";
import type { Lesson } from "../types/lesson";

interface UseLessonsResult {
  lessons: Lesson[];
  loading: boolean;
  /** A translation key (resolve with `t()`), not display text. */
  error: string | null;
}

export function useLessons(): UseLessonsResult {

  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {

    let mounted = true;

    async function loadLessons() {

      try {

        setLoading(true);

        const data = await getLessons();

        if (mounted) {
          setLessons(data);
          setError(null);
        }

      } catch (err) {

        console.warn("Failed to load lessons:", err);

        if (mounted) {
          setLessons([]);
          setError("lessons.loadError");
        }

      } finally {

        if (mounted) {
          setLoading(false);
        }

      }

    }

    loadLessons();

    return () => {
      mounted = false;
    };

  }, []);

  return {
    lessons,
    loading,
    error,
  };
}