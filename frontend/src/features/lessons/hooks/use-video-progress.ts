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
  /** Reports the current playback position to the server (free seeking —
   *  forward and backward jumps are both trusted directly, bounded only
   *  to the video's real duration). `progress` is updated with whatever
   *  the server persisted. */
  reportProgress: (position: number, ended?: boolean) => void;
  markComplete: (ended?: boolean) => Promise<VideoProgress | null>;
  /** Re-fetches a fresh, freshly-signed stream URL for this lesson's
   *  video (and its progress) — used to recover if the player's embedded
   *  stream token has expired or the stream otherwise failed to load. */
  reload: () => void;
}

export function useVideoProgress(lessonId: string): UseVideoProgressResult {
  const [video, setVideo] = useState<LessonVideo | null>(null);
  const [progress, setProgress] = useState<VideoProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const videoRef = useRef<LessonVideo | null>(null);
  const reportingRef = useRef(false);
  // Only the very first load should show the section-level loading state
  // (which unmounts the player entirely). A `reload()` — e.g. recovering
  // from an expired stream token — happens in the background instead,
  // so the player's own "retrying" UI stays visible instead of the whole
  // section flashing to a generic spinner and losing player state.
  const hasLoadedOnceRef = useRef(false);

  useEffect(() => {
    videoRef.current = video;
  }, [video]);

  // Bumped by `reload()` to force the effect below to re-run and fetch a
  // fresh stream URL — e.g. when the player's embedded token has expired.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!lessonId) {
      setLoading(false);
      setError("lessons.loadLessonError");
      return;
    }

    let isMounted = true;

    async function load() {
      try {
        if (!hasLoadedOnceRef.current) setLoading(true);
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
          hasLoadedOnceRef.current = true;
        }
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, [lessonId, reloadToken]);

  const reload = useCallback(() => setReloadToken((n) => n + 1), []);

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
    reload,
  };
}
