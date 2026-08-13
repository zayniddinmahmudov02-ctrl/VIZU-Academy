"use client";

import { useCallback, useRef, useState } from "react";
import axios, { type AxiosProgressEvent } from "axios";

export type UploadState =
  | "IDLE"
  | "UPLOAD_STARTED"
  | "UPLOADING"
  | "SUCCESS"
  | "ERROR"
  | "CANCELLED";

export interface UploadProgress {
  state: UploadState;
  loaded: number;
  total: number | null;
  /** Bytes/sec, or null until enough samples exist to compute a rate. */
  speed: number | null;
  remainingSeconds: number | null;
  error: string | null;
}

const IDLE: UploadProgress = {
  state: "IDLE",
  loaded: 0,
  total: null,
  speed: null,
  remainingSeconds: null,
  error: null,
};

// Samples closer together than this are too noisy to derive a stable
// bytes/sec rate from (chunk-sized bursts, not a real transfer rate).
const MIN_SAMPLE_INTERVAL_MS = 200;

function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  return "Upload failed. Please try again.";
}

/** One real (non-fake) upload-progress tracker, reused by every
 * multipart file upload in the admin CMS instead of each component
 * inventing its own. Wraps whatever axios call the caller performs —
 * `onUploadProgress`/`signal` come from axios's own upload-progress
 * events and AbortController, never a synthetic timer. */
export function useUploadProgress() {
  const [progress, setProgress] = useState<UploadProgress>(IDLE);
  const controllerRef = useRef<AbortController | null>(null);
  const lastSampleRef = useRef<{ loaded: number; time: number } | null>(null);

  const handleProgress = useCallback((event: AxiosProgressEvent) => {
    const now = performance.now();
    const loaded = event.loaded;
    const total = event.total ?? null;

    setProgress((prev) => {
      let speed = prev.speed;
      const last = lastSampleRef.current;

      if (last) {
        const dtMs = now - last.time;
        if (dtMs >= MIN_SAMPLE_INTERVAL_MS) {
          const dl = loaded - last.loaded;
          speed = dtMs > 0 ? (dl / dtMs) * 1000 : speed;
          lastSampleRef.current = { loaded, time: now };
        }
      } else {
        lastSampleRef.current = { loaded, time: now };
      }

      const remainingSeconds =
        total !== null && speed && speed > 0 ? (total - loaded) / speed : null;

      return {
        state: "UPLOADING",
        loaded,
        total,
        speed,
        remainingSeconds,
        error: null,
      };
    });
  }, []);

  /** Runs one upload. `run` receives the axios config fragment
   * (`onUploadProgress` + `signal`) to spread into the real request —
   * the hook never makes the HTTP call itself, so it stays usable with
   * any endpoint/FormData shape. */
  const upload = useCallback(
    async <T,>(
      run: (config: { onUploadProgress: (e: AxiosProgressEvent) => void; signal: AbortSignal }) => Promise<T>,
    ): Promise<T> => {
      const controller = new AbortController();
      controllerRef.current = controller;
      lastSampleRef.current = null;
      setProgress({ ...IDLE, state: "UPLOAD_STARTED" });

      try {
        const result = await run({ onUploadProgress: handleProgress, signal: controller.signal });
        setProgress((prev) => ({ ...prev, state: "SUCCESS" }));
        return result;
      } catch (err) {
        if (controller.signal.aborted) {
          setProgress((prev) => ({ ...prev, state: "CANCELLED" }));
        } else {
          setProgress((prev) => ({ ...prev, state: "ERROR", error: extractErrorMessage(err) }));
        }
        throw err;
      }
    },
    [handleProgress],
  );

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    lastSampleRef.current = null;
    setProgress(IDLE);
  }, []);

  return { progress, upload, cancel, reset };
}
