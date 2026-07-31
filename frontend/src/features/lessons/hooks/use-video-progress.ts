"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { LessonVideo, VideoProgress } from "../types/video";
import {
  completeVideo,
  getLessonVideo,
  getVideoProgress,
  updateVideoProgress,
} from "../services/video-service";

interface UseVideoProgressResult {
  video: LessonVideo | null;
  progress: VideoProgress | null;
  loading: boolean;
  /** A translation key (resolve with `t()`), not display text. */
  error: string | null;
  /** Reports the current playback position to the server. The server is
   *  the source of truth for anti-skip clamping — `progress` is updated
   *  with whatever it actually accepted, which the player should honor
   *  if it differs from what was sent. */
  reportProgress: (position: number, ended?: boolean) => void;
  markComplete: (ended?: boolean) => Promise<VideoProgress | null>;
}

export function useVideoProgress(lessonId: string): UseVideoProgressResult {
  const [video, setVideo] = useState<LessonVideo | null>(null);
  const [progress, setProgress] = useState<VideoProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const videoRef = useRef<LessonVideo | null>(null);
  const reportingRef = useRef(false);

  useEffect(() => {
    videoRef.current = video;
  }, [video]);

  useEffect(() => {
    if (!lessonId) {
      setLoading(false);
      setError("lessons.loadLessonError");
      return;
    }

    let isMounted = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const [videoData, progressData] = await Promise.all([
          getLessonVideo(lessonId),
          getVideoProgress(lessonId),
        ]);

        if (isMounted) {
          setVideo(videoData);
          setProgress(progressData);
        }
      } catch (err) {
        console.warn("Failed to load lesson video:", err);

        if (isMounted) {
          setVideo(null);
          setProgress(null);
          setError("lessons.videoNotAvailable");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, [lessonId]);

  const reportProgress = useCallback((position: number, ended = false) => {
    const current = videoRef.current;
    if (!current || reportingRef.current) return;

    reportingRef.current = true;

    updateVideoProgress(current.id, Math.floor(position), ended)
      .then((updated) => setProgress(updated))
      .catch((err) => console.warn("Failed to report video progress:", err))
      .finally(() => {
        reportingRef.current = false;
      });
  }, []);

  const markComplete = useCallback(async (ended = false) => {
    const current = videoRef.current;
    if (!current) return null;

    try {
      const updated = await completeVideo(current.id, ended);
      setProgress(updated);
      return updated;
    } catch (err) {
      console.warn("Failed to mark video complete:", err);
      return null;
    }
  }, []);

  return {
    video,
    progress,
    loading,
    error,
    reportProgress,
    markComplete,
  };
}
