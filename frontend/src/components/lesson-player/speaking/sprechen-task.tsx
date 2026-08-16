"use client";

import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Clock3, Mic, Pause, Play, RotateCcw, Square } from "lucide-react";

import Button from "@/components/ui/button";
import { resolveMediaUrl } from "@/lib/media";
import {
  getSpeakingAudioBlobUrl,
  getSpeakingResult,
  getSpeakingSubmission,
  uploadSpeakingSubmission,
} from "@/features/admin/services/assessment-service";
import type {
  PublicTask,
  SpeakingResult,
  SpeakingSubmission,
} from "@/features/admin/types/assessment.types";

interface Props {
  task: PublicTask;
  attemptId: string;
  locked: boolean;
  allowResubmit: boolean;
  /** Called once a recording is genuinely uploaded/submitted — lets the
   * parent unlock Lesson Quiz next. */
  onSubmitted?: () => void;
}

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

/** The Sprechen recording flow, exactly per spec's mockup: Aufgabe ->
 * Vorbereitung (countdown, auto-starts recording at 0) -> Aufnahme
 * (START/PAUSE/BEENDEN, auto-stops at speak_seconds if set) -> preview
 * (anhören / erneut aufnehmen / Abgeben). Word-for-word mirrors the only
 * existing MediaRecorder usage in this codebase (the old, backend-less
 * speaking-section.tsx) for the raw recording mechanics, but uploads to
 * the real engine instead of a nonexistent /speakings/evaluate endpoint. */
export default function SprechenTask({ task, attemptId, locked, allowResubmit, onSubmitted }: Props) {
  const [existing, setExisting] = useState<SpeakingSubmission | null | undefined>(undefined);
  const [result, setResult] = useState<SpeakingResult | null>(null);
  const [stage, setStage] = useState<Stage>("idle");
  const [prepRemaining, setPrepRemaining] = useState(task.prep_seconds ?? 0);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [existingAudioUrl, setExistingAudioUrl] = useState<string | null>(null);
  const [playingPreview, setPlayingPreview] = useState(false);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const blobRef = useRef<{ blob: Blob; mimeType: string } | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    getSpeakingSubmission(attemptId, task.id).then((s) => {
      setExisting(s);
      if (s) setStage("submitted");
    });
  }, [attemptId, task.id]);

  useEffect(() => {
    if (existing && existing.status !== "PENDING_REVIEW") {
      getSpeakingResult(attemptId, task.id).then(setResult).catch(() => {});
    }
  }, [attemptId, task.id, existing]);

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
    if (!task.prep_seconds) {
      startRecording();
      return;
    }
    setStage("preparing");
    setPrepRemaining(task.prep_seconds);
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
          if (task.speak_seconds != null && next >= task.speak_seconds) {
            clearTimer();
            recorderRef.current?.stop();
          }
          return next;
        });
      }, 1000);
    } catch {
      setError("Mikrofonzugriff nicht möglich. Bitte Berechtigung erteilen.");
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
        if (task.speak_seconds != null && next >= task.speak_seconds) {
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
      const submitted = await uploadSpeakingSubmission(
        attemptId,
        task.id,
        blobRef.current.blob,
        elapsed,
        extension,
      );
      setExisting(submitted);
      setStage("submitted");
      onSubmitted?.();
    } catch {
      setError("Abgeben fehlgeschlagen.");
      setStage("recorded");
    }
  }

  async function togglePastRecording() {
    if (!existing) return;
    if (!existingAudioUrl) {
      const url = await getSpeakingAudioBlobUrl(existing.id);
      setExistingAudioUrl(url);
    }
  }

  const canReRecord = !locked && allowResubmit;

  return (
    <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border sm:p-8">
      {/* Aufgabe */}
      <h3 className="text-lg font-bold text-text-primary">{task.title}</h3>
      {task.instructions && <p className="mt-1 text-sm text-text-secondary">{task.instructions}</p>}
      {task.content && (
        <div className="prose-editor mt-4 text-text-secondary" dangerouslySetInnerHTML={{ __html: task.content }} />
      )}
      {task.image_url && (
        <img
          src={resolveMediaUrl(task.image_url) ?? undefined}
          alt=""
          className="mt-4 max-h-64 w-full rounded-xl object-cover"
        />
      )}

      <div className="mt-6 border-t border-surface-border pt-6">
        {stage === "submitted" && existing ? (
          <SubmittedView
            submission={existing}
            result={result}
            audioUrl={existingAudioUrl}
            onLoadAudio={togglePastRecording}
            canReRecord={canReRecord}
            onReRecord={reRecord}
          />
        ) : stage === "idle" ? (
          <div className="text-center">
            <p className="mb-3 text-sm font-medium text-text-secondary">Vorbereitung</p>
            {task.prep_seconds != null && (
              <p className="mb-3 text-xs text-text-muted">{task.prep_seconds}s Vorbereitungszeit</p>
            )}
            <Button onClick={startPrep} disabled={locked}>
              START
            </Button>
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
            speakSeconds={task.speak_seconds}
            previewUrl={previewUrl}
            playingPreview={playingPreview}
            audioRef={audioRef}
            onStart={startRecording}
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
    </div>
  );
}

function RecordingPanel({
  stage,
  elapsed,
  speakSeconds,
  previewUrl,
  playingPreview,
  audioRef,
  onStart,
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
  audioRef: React.RefObject<HTMLAudioElement | null>;
  onStart: () => void;
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
        <p className="mb-3 text-sm font-medium text-text-secondary">Aufnahme anhören</p>
        <audio ref={audioRef} src={previewUrl ?? undefined} onEnded={() => {}} className="hidden" />
        <button
          onClick={onTogglePreview}
          className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-accent-blue text-white shadow-md"
        >
          {playingPreview ? <Pause size={22} /> : <Play size={22} />}
        </button>
        <p className="mt-2 text-xs text-text-muted">{formatTime(elapsed)}</p>
        <div className="mt-4 flex justify-center gap-3">
          <Button variant="secondary" onClick={onReRecord} disabled={stage === "submitting"}>
            <RotateCcw size={15} className="mr-1.5" />
            Erneut aufnehmen
          </Button>
          <Button onClick={onSubmit} disabled={stage === "submitting"}>
            {stage === "submitting" ? "Wird abgegeben..." : "Abgeben"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="text-center">
      <Mic className={`mx-auto mb-2 ${stage === "recording" ? "text-danger" : "text-text-muted"}`} size={28} />
      <p className="text-2xl font-bold text-text-primary">
        {formatTime(elapsed)}
        {speakSeconds != null && <span className="text-sm font-normal text-text-muted"> / {formatTime(speakSeconds)}</span>}
      </p>
      <div className="mt-4 flex justify-center gap-3">
        {stage === "idle" || stage === "preparing" ? (
          <Button onClick={onStart}>START</Button>
        ) : stage === "recording" ? (
          <>
            <Button variant="secondary" onClick={onPause}>
              <Pause size={15} className="mr-1.5" />
              PAUSE
            </Button>
            <Button onClick={onStop}>
              <Square size={15} className="mr-1.5" />
              BEENDEN
            </Button>
          </>
        ) : (
          <>
            <Button onClick={onResume}>START</Button>
            <Button variant="secondary" onClick={onStop}>
              <Square size={15} className="mr-1.5" />
              BEENDEN
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

function SubmittedView({
  submission,
  result,
  audioUrl,
  onLoadAudio,
  canReRecord,
  onReRecord,
}: {
  submission: SpeakingSubmission;
  result: SpeakingResult | null;
  audioUrl: string | null;
  onLoadAudio: () => void;
  canReRecord: boolean;
  onReRecord: () => void;
}) {
  return (
    <div className="text-center">
      {audioUrl ? (
        <audio controls src={audioUrl} className="mx-auto w-full max-w-sm" />
      ) : (
        <Button variant="secondary" onClick={onLoadAudio}>
          <Play size={15} className="mr-1.5" />
          Aufnahme anhören
        </Button>
      )}

      {submission.status === "FINAL" && result ? (
        <div className="mx-auto mt-5 max-w-sm rounded-xl bg-surface-card p-5 ring-1 ring-surface-border">
          <div className="flex items-center justify-center gap-2">
            <CheckCircle2 className="text-success" size={20} />
            <span className="text-lg font-bold text-text-primary">{submission.final_score ?? 0} Punkte</span>
          </div>
          {result.show_feedback && result.evaluations[result.evaluations.length - 1]?.feedback && (
            <p className="mt-3 text-left text-sm text-text-secondary">
              {result.evaluations[result.evaluations.length - 1].feedback}
            </p>
          )}
        </div>
      ) : (
        <div className="mt-5 flex items-center justify-center gap-2 text-sm text-text-secondary">
          <Clock3 size={15} />
          Deine Aufnahme wird noch von einem Lehrer bewertet.
        </div>
      )}

      {canReRecord && (
        <Button variant="secondary" onClick={onReRecord} className="mt-4">
          <RotateCcw size={15} className="mr-1.5" />
          Erneut aufnehmen
        </Button>
      )}
    </div>
  );
}
