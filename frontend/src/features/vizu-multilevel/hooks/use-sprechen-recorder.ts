"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type RecorderStatus = "idle" | "requesting" | "recording" | "recorded" | "denied" | "unsupported";

export interface RecordedAnswer {
  blob: Blob;
  url: string;
  duration: number;
}

/** Best compressed format this browser can record (Chrome/Edge: webm/opus,
 * Firefox: ogg/opus, Safari: mp4/aac). */
function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  return ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/webm", "audio/mp4"].find((type) =>
    MediaRecorder.isTypeSupported(type),
  );
}

/** Microphone recording for one Sprechen answer: permission handling,
 * elapsed time with automatic stop at `maxSeconds`, a live AnalyserNode for
 * the waveform, local playback and re-recording. Nothing is uploaded here —
 * the page saves the answer explicitly ("Antwort speichern"). */
export function useSprechenRecorder() {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [answer, setAnswer] = useState<RecordedAnswer | null>(null);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const answerRef = useRef<RecordedAnswer | null>(null);

  const releaseDevices = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    void contextRef.current?.close().catch(() => {});
    contextRef.current = null;
    setAnalyser(null);
  }, []);

  const stop = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    if (recorderRef.current && recorderRef.current.state !== "inactive") recorderRef.current.stop();
  }, []);

  const reset = useCallback(() => {
    stop();
    if (answerRef.current) URL.revokeObjectURL(answerRef.current.url);
    answerRef.current = null;
    setAnswer(null);
    setElapsed(0);
    setStatus("idle");
  }, [stop]);

  const start = useCallback(
    async (maxSeconds: number) => {
      if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
        setStatus("unsupported");
        return;
      }
      if (answerRef.current) URL.revokeObjectURL(answerRef.current.url);
      answerRef.current = null;
      setAnswer(null);
      setStatus("requesting");
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      } catch {
        setStatus("denied");
        return;
      }
      streamRef.current = stream;

      try {
        const context = new AudioContext();
        const node = context.createAnalyser();
        node.fftSize = 256;
        context.createMediaStreamSource(stream).connect(node);
        contextRef.current = context;
        setAnalyser(node);
      } catch {
        /* the waveform is optional — recording still works */
      }

      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      const chunks: Blob[] = [];
      const startedAt = Date.now();
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.push(event.data);
      };
      recorder.onstop = () => {
        const duration = Math.max(1, Math.round((Date.now() - startedAt) / 1000));
        const blob = new Blob(chunks, { type: (recorder.mimeType || mimeType || "audio/webm").split(";")[0] });
        const recorded = { blob, url: URL.createObjectURL(blob), duration };
        answerRef.current = recorded;
        setAnswer(recorded);
        setElapsed(duration);
        setStatus("recorded");
        releaseDevices();
      };
      recorderRef.current = recorder;
      recorder.start(1000);
      setElapsed(0);
      setStatus("recording");
      timerRef.current = setInterval(() => {
        const seconds = Math.floor((Date.now() - startedAt) / 1000);
        setElapsed(seconds);
        if (seconds >= maxSeconds) stop();
      }, 250);
    },
    [releaseDevices, stop],
  );

  useEffect(() => {
    return () => {
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.onstop = null;
        recorderRef.current.stop();
      }
      releaseDevices();
      if (answerRef.current) URL.revokeObjectURL(answerRef.current.url);
    };
  }, [releaseDevices]);

  return { status, elapsed, answer, analyser, start, stop, reset };
}
