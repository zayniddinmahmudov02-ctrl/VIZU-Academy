"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api";

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
  /** Why loading failed: "not_found" = the backend has no playable video
   *  for this lesson (GET /videos/by-lesson 404 — no published video, or
   *  its stored file is missing), "forbidden" = 403 (no access), "failed"
   *  = anything else (network, 5xx) — worth a retry. */
  errorKind: VideoLoadErrorKind | null;
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
export type VideoLoadErrorKind = "not_found" | "forbidden" | "failed";

function classifyLoadError(err: unknown): VideoLoadErrorKind {
  if (err instanceof ApiError && err.status === 404) return "not_found";
  if (err instanceof ApiError && err.status === 403) return "forbidden";
  return "failed";
}

const ERROR_KEYS: Record<VideoLoadErrorKind, string> = {
  not_found: "lessons.videoNotAvailable",
  forbidden: "lessons.videoAccessDenied",
  failed: "lessons.videoLoadError",
};

export function useVideoProgress(lessonId: string): UseVideoProgressResult {
  const [video, setVideo] = useState<LessonVideo | null>(null);
  const [progress, setProgress] = useState<VideoProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorKind, setErrorKind] = useState<VideoLoadErrorKind | null>(null);

  const videoRef = useRef<LessonVideo | null>(null);
  const reportingRef = useRef(false);
  const inflightReportRef = useRef<Promise<void> | null>(null);
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
      setErrorKind("failed");
      return;
    }

    let isMounted = true;

    async function load() {
      try {
        if (!hasLoadedOnceRef.current) setLoading(true);
        setErrorKind(null);

        const [videoData, progressData] = await Promise.all([
          getLessonVideo(lessonId),
          getVideoProgress(lessonId),
        ]);

        if (isMounted) {
          setVideo(videoData);
          setProgress(progressData);
        }
      } catch (err) {
        const kind = classifyLoadError(err);
        // 404 = this lesson has no playable video (a data state the UI
        // shows as such), not a client failure worth a console warning.
        if (kind !== "not_found") console.warn("Failed to load lesson video:", err);

        if (isMounted) {
          setVideo(null);
          setProgress(null);
          setErrorKind(kind);
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

    inflightReportRef.current = updateVideoProgress(current.id, Math.floor(position), ended)
      .then((updated) => setProgress(updated))
      .catch((err) => console.warn("Failed to report video progress:", err))
      .finally(() => {
        reportingRef.current = false;
        inflightReportRef.current = null;
      });
  }, []);

  const markComplete = useCallback(async (ended = false) => {
    const current = videoRef.current;
    if (!current) return null;

    // POST /videos/complete is judged against the server-side watch
    // progress — sent while the report for the same position is still in
    // flight it can arrive first (400 "No watch progress recorded" / too
    // little watched) and the completion would be lost.
    await inflightReportRef.current;

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
    error: errorKind ? ERROR_KEYS[errorKind] : null,
    errorKind,
    reportProgress,
    markComplete,
    reload,
  };
}
