"use client";

import { useEffect, useState } from "react";

import { getVideoProgress } from "../services/video-service";

/** null while loading, then whether this lesson's video has been
 *  completed — the single source of truth `LessonActivityGate` locks
 *  the rest of the lesson behind. A failed/unauthorized lookup is
 *  treated as "not completed" (locked), never as "completed". */
export function useVideoCompletion(lessonId: string): boolean | null {
  const [completed, setCompleted] = useState<boolean | null>(null);

  useEffect(() => {
    if (!lessonId) {
      setCompleted(false);
      return;
    }

    let isMounted = true;

    getVideoProgress(lessonId)
      .then((progress) => {
        if (isMounted) setCompleted(progress.completed);
      })
      .catch((err) => {
        console.warn("Failed to load video completion status:", err);
        if (isMounted) setCompleted(false);
      });

    return () => {
      isMounted = false;
    };
  }, [lessonId]);

  return completed;
}
