"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Clock, Info, Mic, Pause, Play, RotateCcw, Square } from "lucide-react";

import type { LessonSpeaking } from "@/features/lessons/services/speaking-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import {
  getMySpeakingSubmission,
  getSpeakingSubmissionAudioBlobUrl,
  retrySpeakingEvaluation,
  submitSpeakingRecording,
  type SpeakingOwnSubmission,
} from "@/features/lessons/services/speaking-submission-service";

import AiEvaluationCard from "../common/ai-evaluation-card";

type Stage = "idle" | "preparing" | "recording" | "paused" | "recorded" | "submitting";

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

const noopSubscribe = () => () => {};

function errorCode(err: unknown): string {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  return data ? String(data.message ?? data.detail ?? "") : "";
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
  const { t } = useTranslation();
  const ai = !!speaking.ai_evaluation_enabled;
  const minDuration = speaking.min_duration_seconds ?? 0;

  const { data: existing } = useQuery({
    queryKey: ["speaking-submission", speaking.id],
    queryFn: () => getMySpeakingSubmission(speaking.id),
    // poll while STT + AI evaluation run in the background
    refetchInterval: (query) =>
      ai && ["SUBMITTED", "EVALUATING"].includes(query.state.data?.status ?? "") ? 3000 : false,
  });

  const [stage, setStage] = useState<Stage>("idle");
  const [prepRemaining, setPrepRemaining] = useState(speaking.preparation_time ?? 0);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [existingAudioUrl, setExistingAudioUrl] = useState<string | null>(null);
  const [playingPreview, setPlayingPreview] = useState(false);
  const mediaRecorderSupported = useSyncExternalStore(
    noopSubscribe,
    () => typeof window.MediaRecorder !== "undefined",
    () => true,
  );
  const [pauseSupported, setPauseSupported] = useState(true);
  // true while the student records a new version over an existing submission
  const [reRecording, setReRecording] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const blobRef = useRef<{ blob: Blob; mimeType: string } | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      clearTimer();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
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
      setError(t("lessons.micDenied"));
      setStage("idle");
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
    setError(null);
    setStage("idle");
    if (existing) setReRecording(true);
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
    if (ai && minDuration && elapsed < minDuration) {
      setError(t("lessons.recordingTooShort", { n: minDuration }));
      return;
    }
    setStage("submitting");
    setError(null);
    try {
      const extension = EXTENSION_BY_MIME[blobRef.current.mimeType.split(";")[0]] ?? "webm";
      const result = await submitSpeakingRecording(speaking.id, blobRef.current.blob, elapsed, extension);
      queryClient.setQueryData(["speaking-submission", speaking.id], result);
      queryClient.invalidateQueries({ queryKey: ["section-gate"] });
      queryClient.invalidateQueries({ queryKey: ["lesson-skill-results", speaking.lesson_id] });
      if (existingAudioUrl) URL.revokeObjectURL(existingAudioUrl);
      setExistingAudioUrl(null);
      setReRecording(false);
      setStage("idle");
    } catch (err) {
      const code = errorCode(err);
      setError(
        code === "RECORDING_TOO_SHORT"
          ? t("lessons.recordingTooShort", { n: minDuration })
          : code === "RECORDING_TOO_LONG"
            ? t("lessons.recordingTooLong")
            : code === "MAX_ATTEMPTS_REACHED"
              ? t("lessons.maxAttemptsReached")
              : code === "EVALUATION_IN_PROGRESS"
                ? t("lessons.aiPending")
                : t("lessons.sendFailed"),
      );
      setStage("recorded");
    }
  }

  async function retryEvaluation() {
    setRetrying(true);
    setError(null);
    try {
      const result = await retrySpeakingEvaluation(speaking.id);
      queryClient.setQueryData(["speaking-submission", speaking.id], result);
      await queryClient.invalidateQueries({ queryKey: ["speaking-submission", speaking.id] });
    } catch {
      setError(t("lessons.loadError"));
    } finally {
      setRetrying(false);
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

  const attemptsUsed = existing?.attempt_count ?? 0;
  const maxAttempts = speaking.max_attempts ?? 1;
  const attemptsLeft = Math.max(0, maxAttempts - attemptsUsed);
  // AI tasks: a new version after a result / failed run while attempts
  // remain, never while the evaluation runs. Teacher-graded tasks keep
  // the old rule (only after NEEDS_REVISION).
  const canReRecord = !existing
    ? true
    : ai
      ? (existing.status === "GRADED" || existing.status === "EVALUATION_FAILED" || existing.status === "NEEDS_REVISION") && attemptsLeft > 0
      : existing.status === "NEEDS_REVISION";
  const showSubmitted = !!existing && !reRecording;

  return (
    <div className="mt-4 rounded-2xl bg-surface-card p-5 ring-1 ring-surface-border" data-testid="speaking-recorder">
      {showSubmitted && existing ? (
        <SubmittedView
          submission={existing}
          ai={ai}
          attemptsUsed={attemptsUsed}
          maxAttempts={maxAttempts}
          audioUrl={existingAudioUrl}
          onLoadAudio={loadExistingAudio}
          canReRecord={canReRecord}
          onReRecord={reRecord}
          onRetry={retryEvaluation}
          retrying={retrying}
        />
      ) : stage === "idle" ? (
        <div className="flex flex-col items-center text-center">
          <Mic className="mx-auto mb-2 text-text-muted" size={22} />
          <p className="mb-3 flex max-w-md items-start gap-1.5 text-left text-xs text-text-secondary" data-testid="mic-info">
            <Info size={14} className="mt-0.5 shrink-0 text-accent-blue" />
            {t("lessons.micPermissionInfo")}
          </p>
          {speaking.preparation_time > 0 && (
            <p className="mb-1 text-xs text-text-muted">{speaking.preparation_time}s Vorbereitungszeit</p>
          )}
          {ai && minDuration > 0 && <p className="mb-3 text-xs text-text-muted">{t("lessons.minDuration", { n: minDuration })}</p>}
          <div className="flex flex-wrap justify-center gap-2">
            <button
              onClick={startPrep}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
              data-testid="speaking-start"
            >
              ● Aufnahme starten
            </button>
            {reRecording && (
              <button
                onClick={() => setReRecording(false)}
                className="min-h-11 rounded-xl px-4 text-sm font-semibold text-text-secondary ring-1 ring-surface-border"
              >
                {t("lessons.confirmNo")}
              </button>
            )}
          </div>
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
          reRecordLabel={t("lessons.newRecording")}
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
  reRecordLabel,
}: {
  reRecordLabel: string;
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
        <audio ref={audioRef} src={previewUrl ?? undefined} className="hidden" />
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
            <RotateCcw size={14} /> {reRecordLabel}
          </button>
          <button
            onClick={onSubmit}
            disabled={stage === "submitting"}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            data-testid="speaking-submit"
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
  ai,
  attemptsUsed,
  maxAttempts,
  audioUrl,
  onLoadAudio,
  canReRecord,
  onReRecord,
  onRetry,
  retrying,
}: {
  submission: SpeakingOwnSubmission;
  ai: boolean;
  attemptsUsed: number;
  maxAttempts: number;
  audioUrl: string | null;
  onLoadAudio: () => void;
  canReRecord: boolean;
  onReRecord: () => void;
  onRetry: () => void;
  retrying: boolean;
}) {
  const { t } = useTranslation();
  if (ai) {
    return (
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="flex items-center gap-1.5 text-sm font-semibold text-success">
            <CheckCircle2 size={16} /> Aufgabe gesendet
          </p>
          {attemptsUsed > 0 && (
            <span className="text-xs font-semibold text-text-muted" data-testid="speaking-attempts">
              {t("lessons.attemptOf", { n: attemptsUsed, max: maxAttempts })}
            </span>
          )}
        </div>
        {audioUrl ? (
          <audio controls src={audioUrl} className="w-full" />
        ) : (
          <button
            onClick={onLoadAudio}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border"
          >
            <Play size={14} /> Aufnahme anhören
          </button>
        )}
        {submission.status === "NEEDS_REVISION" ? (
          <div className="rounded-xl bg-warning/10 p-4 text-left text-sm text-warning">
            <strong>Zur Überarbeitung:</strong> {submission.feedback}
          </div>
        ) : (
          <AiEvaluationCard
            status={submission.status}
            score={submission.score}
            aiScore={submission.ai_score ?? null}
            evaluation={submission.ai_evaluation ?? null}
            onRetry={onRetry}
            retrying={retrying}
            showTranscript
          />
        )}
        {submission.status === "GRADED" && submission.feedback && !submission.ai_evaluation && (
          <p className="text-sm text-text-secondary">{submission.feedback}</p>
        )}
        {canReRecord ? (
          <button
            onClick={onReRecord}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border"
            data-testid="speaking-rerecord"
          >
            <RotateCcw size={14} /> {t("lessons.newRecording")}
          </button>
        ) : (
          (submission.status === "GRADED" || submission.status === "EVALUATION_FAILED") && (
            <p className="text-xs text-text-muted">{t("lessons.maxAttemptsReached")}</p>
          )
        )}
      </div>
    );
  }
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
        <p className="mx-auto mt-5 inline-flex items-center gap-1.5 rounded-xl bg-warning/10 px-4 py-2 text-sm font-semibold text-warning">
          <Clock size={15} />
          {t("lessons.statusPending")}
        </p>
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
