"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Mic, Pause, Play, RotateCcw, Square } from "lucide-react";

import type { LessonSpeaking } from "@/features/lessons/services/speaking-service";
import {
  getMySpeakingSubmission,
  getSpeakingSubmissionAudioBlobUrl,
  submitSpeakingRecording,
  type SpeakingOwnSubmission,
} from "@/features/lessons/services/speaking-submission-service";

type Stage = "idle" | "preparing" | "recording" | "paused" | "recorded" | "submitting" | "submitted";

const EXTENSION_BY_MIME: Record<string, string> = {
  "audio/webm": "webm",
  "audio/ogg": "ogg",
  "audio/mp4": "m4a",
  "audio/mpeg": "mp3",
  "audio/wav": "wav",
};

function pickRecorderMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
  for (const type of candidates) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) return type;
  }
  return "";
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/** The real Sprechen recorder for the legacy per-lesson Speaking task —
 * mechanically the same MediaRecorder flow already proven in this
 * codebase (Vorbereitung/sprechen-task.tsx: prep countdown ->
 * record/pause/resume -> auto-stop at speaking_time -> preview ->
 * re-record or send), reused rather than reinvented, just wired to the
 * new legacy StudentSpeaking endpoints instead of the Assessment
 * Engine's. Real backend upload, real private storage, real teacher
 * review — no fake recorder. */
export default function SpeakingTaskRecorder({ speaking }: { speaking: LessonSpeaking }) {
  const queryClient = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ["speaking-submission", speaking.id],
    queryFn: () => getMySpeakingSubmission(speaking.id),
  });

  const [stage, setStage] = useState<Stage>("idle");
  const [prepRemaining, setPrepRemaining] = useState(speaking.preparation_time ?? 0);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [existingAudioUrl, setExistingAudioUrl] = useState<string | null>(null);
  const [playingPreview, setPlayingPreview] = useState(false);
  const [mediaRecorderSupported, setMediaRecorderSupported] = useState(true);
  const [pauseSupported, setPauseSupported] = useState(true);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const blobRef = useRef<{ blob: Blob; mimeType: string } | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (existing) setStage("submitted");
  }, [existing]);

  useEffect(() => {
    setMediaRecorderSupported(typeof window !== "undefined" && typeof window.MediaRecorder !== "undefined");
  }, []);

  useEffect(() => {
    return () => {
      clearTimer();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function clearTimer() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }

  function startPrep() {
    if (!speaking.preparation_time) {
      startRecording();
      return;
    }
    setStage("preparing");
    setPrepRemaining(speaking.preparation_time);
    clearTimer();
    intervalRef.current = setInterval(() => {
      setPrepRemaining((prev) => {
        if (prev <= 1) {
          clearTimer();
          startRecording();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = pickRecorderMimeType();
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      setPauseSupported(typeof recorder.pause === "function");
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const usedMimeType = recorder.mimeType || mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: usedMimeType });
        blobRef.current = { blob, mimeType: usedMimeType };
        setPreviewUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((t) => t.stop());
        setStage("recorded");
      };
      recorderRef.current = recorder;
      recorder.start();
      setStage("recording");
      setElapsed(0);
      clearTimer();
      intervalRef.current = setInterval(() => {
        setElapsed((prev) => {
          const next = prev + 1;
          if (speaking.speaking_time != null && next >= speaking.speaking_time) {
            clearTimer();
            recorderRef.current?.stop();
          }
          return next;
        });
      }, 1000);
    } catch {
      setError("Der Zugriff auf das Mikrofon wurde verweigert.");
    }
  }

  function pauseRecording() {
    recorderRef.current?.pause();
    clearTimer();
    setStage("paused");
  }

  function resumeRecording() {
    recorderRef.current?.resume();
    setStage("recording");
    intervalRef.current = setInterval(() => {
      setElapsed((prev) => {
        const next = prev + 1;
        if (speaking.speaking_time != null && next >= speaking.speaking_time) {
          clearTimer();
          recorderRef.current?.stop();
        }
        return next;
      });
    }, 1000);
  }

  function stopRecording() {
    clearTimer();
    recorderRef.current?.stop();
  }

  function reRecord() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    blobRef.current = null;
    setElapsed(0);
    setStage("idle");
  }

  async function togglePreviewPlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playingPreview) {
      audio.pause();
      setPlayingPreview(false);
    } else {
      audio.play();
      setPlayingPreview(true);
    }
  }

  async function handleSubmit() {
    if (!blobRef.current) return;
    setStage("submitting");
    setError(null);
    try {
      const extension = EXTENSION_BY_MIME[blobRef.current.mimeType.split(";")[0]] ?? "webm";
      const result = await submitSpeakingRecording(speaking.id, blobRef.current.blob, elapsed, extension);
      queryClient.setQueryData(["speaking-submission", speaking.id], result);
      queryClient.invalidateQueries({ queryKey: ["section-gate"] });
      setStage("submitted");
    } catch {
      setError("Die Aufnahme konnte nicht gesendet werden.");
      setStage("recorded");
    }
  }

  async function loadExistingAudio() {
    if (!existing || existingAudioUrl) return;
    const url = await getSpeakingSubmissionAudioBlobUrl(existing.id);
    setExistingAudioUrl(url);
  }

  if (!mediaRecorderSupported) {
    return (
      <div className="mt-4 rounded-xl bg-surface-hover p-4 text-center text-sm text-text-secondary ring-1 ring-surface-border">
        Audioaufnahme wird von diesem Browser nicht unterstützt.
      </div>
    );
  }

  const canReRecord = !existing || existing.status === "NEEDS_REVISION";

  return (
    <div className="mt-4 rounded-2xl bg-surface-card p-5 ring-1 ring-surface-border">
      {stage === "submitted" && existing ? (
        <SubmittedView
          submission={existing}
          audioUrl={existingAudioUrl}
          onLoadAudio={loadExistingAudio}
          canReRecord={canReRecord}
          onReRecord={reRecord}
        />
      ) : stage === "idle" ? (
        <div className="text-center">
          <Mic className="mx-auto mb-2 text-text-muted" size={22} />
          {speaking.preparation_time > 0 && (
            <p className="mb-3 text-xs text-text-muted">{speaking.preparation_time}s Vorbereitungszeit</p>
          )}
          <button
            onClick={startPrep}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
          >
            ● Aufnahme starten
          </button>
        </div>
      ) : stage === "preparing" ? (
        <div className="text-center">
          <p className="mb-2 text-sm font-medium text-text-secondary">Vorbereitung läuft...</p>
          <p className="text-3xl font-bold text-accent-blue">{formatTime(prepRemaining)}</p>
        </div>
      ) : (
        <RecordingPanel
          stage={stage}
          elapsed={elapsed}
          speakSeconds={speaking.speaking_time}
          previewUrl={previewUrl}
          playingPreview={playingPreview}
          pauseSupported={pauseSupported}
          audioRef={audioRef}
          onPause={pauseRecording}
          onResume={resumeRecording}
          onStop={stopRecording}
          onTogglePreview={togglePreviewPlay}
          onReRecord={reRecord}
          onSubmit={handleSubmit}
        />
      )}
      {error && <p className="mt-3 text-center text-xs text-danger">{error}</p>}
    </div>
  );
}

function RecordingPanel({
  stage,
  elapsed,
  speakSeconds,
  previewUrl,
  playingPreview,
  pauseSupported,
  audioRef,
  onPause,
  onResume,
  onStop,
  onTogglePreview,
  onReRecord,
  onSubmit,
}: {
  stage: Stage;
  elapsed: number;
  speakSeconds: number | null;
  previewUrl: string | null;
  playingPreview: boolean;
  pauseSupported: boolean;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onTogglePreview: () => void;
  onReRecord: () => void;
  onSubmit: () => void;
}) {
  if (stage === "recorded" || stage === "submitting") {
    return (
      <div className="text-center">
        <p className="mb-3 text-sm font-medium text-text-secondary">Aufnahme fertig</p>
        <audio ref={audioRef} src={previewUrl ?? undefined} onEnded={() => {}} className="hidden" />
        <button
          onClick={onTogglePreview}
          aria-label={playingPreview ? "Pause" : "Anhören"}
          className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-accent-blue text-white shadow-md"
        >
          {playingPreview ? <Pause size={22} /> : <Play size={22} />}
        </button>
        <p className="mt-2 text-xs text-text-muted">{formatTime(elapsed)}</p>
        <div className="mt-4 flex flex-wrap justify-center gap-3">
          <button
            onClick={onReRecord}
            disabled={stage === "submitting"}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border disabled:opacity-60"
          >
            <RotateCcw size={14} /> Neu aufnehmen
          </button>
          <button
            onClick={onSubmit}
            disabled={stage === "submitting"}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            {stage === "submitting" ? "Wird gesendet..." : "Aufgabe senden"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="text-center">
      <p className={`flex items-center justify-center gap-1.5 text-sm font-semibold ${stage === "recording" ? "text-danger" : "text-text-muted"}`}>
        <span className={stage === "recording" ? "animate-pulse" : ""}>🔴</span>
        {stage === "recording" ? "Aufnahme läuft" : "Aufnahme pausiert"}
      </p>
      <p className="mt-1 text-2xl font-bold text-text-primary">
        {formatTime(elapsed)}
        {speakSeconds != null && <span className="text-sm font-normal text-text-muted"> / {formatTime(speakSeconds)}</span>}
      </p>
      <div className="mt-4 flex justify-center gap-3">
        {stage === "recording" ? (
          <>
            {pauseSupported && (
              <button
                onClick={onPause}
                className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border"
              >
                ⏸ Pause
              </button>
            )}
            <button
              onClick={onStop}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white"
            >
              <Square size={14} /> Stop
            </button>
          </>
        ) : (
          <>
            <button
              onClick={onResume}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white"
            >
              ▶ Fortsetzen
            </button>
            <button
              onClick={onStop}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border"
            >
              <Square size={14} /> Stop
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function SubmittedView({
  submission,
  audioUrl,
  onLoadAudio,
  canReRecord,
  onReRecord,
}: {
  submission: SpeakingOwnSubmission;
  audioUrl: string | null;
  onLoadAudio: () => void;
  canReRecord: boolean;
  onReRecord: () => void;
}) {
  return (
    <div className="text-center">
      <p className="mb-3 flex items-center justify-center gap-1.5 text-sm font-semibold text-success">
        <CheckCircle2 size={16} /> Aufgabe gesendet
      </p>

      {audioUrl ? (
        <audio controls src={audioUrl} className="mx-auto w-full max-w-sm" />
      ) : (
        <button
          onClick={onLoadAudio}
          className="mx-auto flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border"
        >
          <Play size={14} /> Aufnahme anhören
        </button>
      )}

      {submission.status === "GRADED" ? (
        <div className="mx-auto mt-5 max-w-sm rounded-xl bg-surface-hover p-5 ring-1 ring-surface-border">
          <p className="text-lg font-bold text-text-primary">Bewertet: {submission.score}/100</p>
          {submission.feedback && <p className="mt-3 text-left text-sm text-text-secondary">{submission.feedback}</p>}
        </div>
      ) : submission.status === "NEEDS_REVISION" ? (
        <div className="mx-auto mt-5 max-w-sm rounded-xl bg-warning/10 p-5 text-left text-sm text-warning">
          <strong>Zur Überarbeitung:</strong> {submission.feedback}
        </div>
      ) : (
        <p className="mt-5 text-sm text-text-secondary">Deine Aufnahme wird noch von einem Lehrer bewertet.</p>
      )}

      {canReRecord && (
        <button
          onClick={onReRecord}
          className="mx-auto mt-4 flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border"
        >
          <RotateCcw size={14} /> Neu aufnehmen
        </button>
      )}
    </div>
  );
}
