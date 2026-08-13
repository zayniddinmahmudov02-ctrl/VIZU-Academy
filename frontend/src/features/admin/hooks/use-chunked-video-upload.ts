"use client";

import { useCallback, useRef, useState } from "react";
import axios from "axios";

import type { Video } from "../types/content.types";
import { uploadVideoChunked, type ChunkedUploadMetadata } from "../lib/chunked-video-upload";
import type { UploadProgress } from "./use-upload-progress";

const IDLE: UploadProgress = {
  state: "IDLE",
  loaded: 0,
  total: null,
  speed: null,
  remainingSeconds: null,
  error: null,
};

// Same noise-floor as use-upload-progress's single-request version —
// samples closer together than this don't produce a stable bytes/sec
// rate, they just reflect one chunk's onUploadProgress bursts.
const MIN_SAMPLE_INTERVAL_MS = 200;

function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data;
    const text = data?.message ?? data?.detail;
    if (typeof text === "string" && text.trim()) return text;
  }
  return "Upload failed. Please try again.";
}

/** Same UploadProgress shape/semantics as useUploadProgress (so both
 *  plug into the same <UploadProgressPanel> unchanged), but driven by
 *  uploadVideoChunked's cumulative-bytes-across-many-requests callback
 *  instead of a single axios call's onUploadProgress event. */
export function useChunkedVideoUpload() {
  const [progress, setProgress] = useState<UploadProgress>(IDLE);
  const controllerRef = useRef<AbortController | null>(null);
  const lastSampleRef = useRef<{ loaded: number; time: number } | null>(null);

  const handleProgress = useCallback((loaded: number, total: number) => {
    const now = performance.now();

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

      const remainingSeconds = speed && speed > 0 ? (total - loaded) / speed : null;

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

  const upload = useCallback(
    async (file: File, metadata: ChunkedUploadMetadata): Promise<Video> => {
      const controller = new AbortController();
      controllerRef.current = controller;
      lastSampleRef.current = null;
      setProgress({ ...IDLE, state: "UPLOAD_STARTED", total: file.size });

      try {
        const result = await uploadVideoChunked(file, metadata, {
          onProgress: handleProgress,
          signal: controller.signal,
        });
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
