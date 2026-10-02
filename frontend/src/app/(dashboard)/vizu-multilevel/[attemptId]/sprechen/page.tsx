"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Mic, RotateCcw, Square } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import { SectionError, SectionLoading, SectionPreparing } from "@/features/vizu-multilevel/components/section-states";
import VizuMultilevelStepShell from "@/features/vizu-multilevel/components/step-shell";
import { getSkillMeta, nextStepPath } from "@/features/vizu-multilevel/constants/skills";
import VizuMultilevelProgressHeader from "@/features/vizu-multilevel/components/progress-header";
import {
  apiErrorCode,
  isConflict,
  minAnswersRequired,
  useVizuMultilevelSection,
} from "@/features/vizu-multilevel/hooks/use-section";
import {
  getVizuMultilevelSprechenSubmissions,
  getVizuMultilevelSprechenTasks,
  submitVizuMultilevelSprechen,
  uploadVizuMultilevelSprechenRecording,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";

interface Recording {
  blob: Blob;
  url: string;
  duration: number;
  uploaded: boolean;
}

function formatClock(totalSeconds: number): string {
  const mm = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const ss = String(totalSeconds % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

/** Sprechen step. The student records one answer per Aufgabe with the
 * browser's MediaRecorder; recordings are uploaded to protected storage
 * (only the student and teachers can play them back) when moving on or
 * finishing. The 20-minute window is owned by the server. Nothing is graded
 * automatically — a teacher grades the recordings — so no level or score is
 * shown here. */
export default function VizuMultilevelSprechenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("sprechen")!;

  const gate = useVizuMultilevelSection(attemptId, "sprechen");
  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-multilevel-sprechen-tasks"],
    queryFn: getVizuMultilevelSprechenTasks,
  });
  const { data: existing } = useQuery({
    queryKey: ["vizu-multilevel-sprechen-submissions", attemptId],
    queryFn: () => getVizuMultilevelSprechenSubmissions(attemptId),
  });

  const [taskIndex, setTaskIndex] = useState(0);
  const [recordings, setRecordings] = useState<Record<string, Recording>>({});
  const [recordingTaskId, setRecordingTaskId] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [micError, setMicError] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recordingsRef = useRef(recordings);
  const submittingRef = useRef(false);

  useEffect(() => {
    recordingsRef.current = recordings;
  }, [recordings]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
      Object.values(recordingsRef.current).forEach((r) => URL.revokeObjectURL(r.url));
    };
  }, []);

  const uploadedTaskIds = new Set((existing ?? []).map((s) => s.task_id));
  const recordedCount = (tasks ?? []).filter((x) => recordings[x.id] || uploadedTaskIds.has(x.id)).length;
  const minRequired = minAnswersRequired(tasks?.length ?? 0);
  const canFinish = recordedCount >= minRequired;

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    if (recorderRef.current && recorderRef.current.state !== "inactive") recorderRef.current.stop();
  }

  async function startRecording(taskId: string, maxSeconds: number) {
    setMicError(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : undefined;
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      const startedAt = Date.now();
      recorder.onstop = () => {
        const duration = Math.max(1, Math.round((Date.now() - startedAt) / 1000));
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());
        setRecordings((prev) => {
          if (prev[taskId]) URL.revokeObjectURL(prev[taskId].url);
          return { ...prev, [taskId]: { blob, url: URL.createObjectURL(blob), duration, uploaded: false } };
        });
        setRecordingTaskId(null);
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecordingTaskId(taskId);
      setElapsed(0);
      timerRef.current = setInterval(() => {
        const seconds = Math.round((Date.now() - startedAt) / 1000);
        setElapsed(seconds);
        if (seconds >= maxSeconds) stopRecording();
      }, 500);
    } catch {
      setMicError(true);
    }
  }

  function discardRecording(taskId: string) {
    setRecordings((prev) => {
      if (prev[taskId]) URL.revokeObjectURL(prev[taskId].url);
      const next = { ...prev };
      delete next[taskId];
      return next;
    });
  }

  /** Uploads every recording that has not reached the server yet. A closed
   * window (409) is not an error here — the final submit still proceeds. */
  async function uploadPending() {
    for (const [taskId, rec] of Object.entries(recordingsRef.current)) {
      if (rec.uploaded) continue;
      try {
        await uploadVizuMultilevelSprechenRecording(attemptId, taskId, rec.blob, rec.duration);
        setRecordings((prev) => (prev[taskId] ? { ...prev, [taskId]: { ...prev[taskId], uploaded: true } } : prev));
      } catch (error) {
        if (!isConflict(error)) throw error;
      }
    }
  }

  const submitMutation = useMutation({
    mutationFn: async () => {
      stopRecording();
      await uploadPending();
      await submitVizuMultilevelSprechen(attemptId);
    },
    onSuccess: () => router.push(nextStepPath(attemptId, "sprechen")),
    onError: (error) => {
      if (apiErrorCode(error) === "MIN_ANSWERS_REQUIRED") {
        submittingRef.current = false;
        setSubmitError(t("vizuMultilevel.minRequiredError", { min: minRequired }));
        return;
      }
      if (isConflict(error)) {
        router.push(nextStepPath(attemptId, "sprechen"));
        return;
      }
      submittingRef.current = false;
      setSubmitError(t("vizuMultilevel.submitFailed"));
    },
  });

  function handleSubmit() {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setSubmitError(null);
    setConfirmOpen(false);
    // Let a running recording flush its final chunk before uploading.
    setTimeout(() => submitMutation.mutate(), recorderRef.current?.state === "recording" ? 400 : 0);
  }

  if (gate.status === "error") {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionError />
      </VizuMultilevelStepShell>
    );
  }
  if (gate.status === "loading" || isLoading || !tasks) {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionLoading />
      </VizuMultilevelStepShell>
    );
  }

  const task = tasks[taskIndex];
  const isLastTask = taskIndex >= tasks.length - 1;
  const recording = task ? recordings[task.id] : undefined;
  const isRecordingThis = task ? recordingTaskId === task.id : false;
  const alreadySent = task ? uploadedTaskIds.has(task.id) : false;

  return (
    <VizuMultilevelStepShell
      skill={skill}
      initialSeconds={gate.secondsRemaining}
      onTimerExpire={handleSubmit}
      onFinishClick={() => setConfirmOpen(true)}
      footer={
        <div className="flex flex-wrap items-center justify-end gap-2">
          {task && taskIndex > 0 && (
            <Button variant="secondary" onClick={() => setTaskIndex((i) => i - 1)} disabled={isRecordingThis}>
              <ArrowLeft size={16} />
              {t("vizuMultilevel.previous")}
            </Button>
          )}
          <Button
            onClick={() => (!task || isLastTask ? setConfirmOpen(true) : setTaskIndex((i) => i + 1))}
            disabled={isRecordingThis || submitMutation.isPending}
          >
            {!task || isLastTask ? t("vizuMultilevel.sprechenAbsenden") : t("vizuMultilevel.next")}
          </Button>
        </div>
      }
    >
      {!task ? (
        <SectionPreparing skill="sprechen" />
      ) : (
        <div className="space-y-4">
          <VizuMultilevelProgressHeader
            positionLabel={t("vizuMultilevel.aufgabePos", { current: taskIndex + 1, total: tasks.length })}
            answered={recordedCount}
            total={tasks.length}
            minRequired={minRequired}
          />

          <div className="flex items-start gap-3 rounded-2xl bg-surface-hover/60 p-4 ring-1 ring-surface-border">
            <Mic size={18} className="mt-0.5 shrink-0 text-text-muted" />
            <div>
              <p className="text-sm font-bold text-text-primary">{task.title}</p>
              <p className="mt-1 whitespace-pre-line text-sm text-text-secondary">{task.instruction}</p>
              {task.preparation_text && (
                <p className="mt-2 whitespace-pre-line text-xs text-text-muted">{task.preparation_text}</p>
              )}
              <p className="mt-2 text-xs text-text-muted">
                {t("vizuMultilevel.maxRecording", { seconds: task.max_seconds })}
              </p>
            </div>
          </div>

          <div className="flex flex-col items-center gap-4 rounded-2xl bg-surface-hover/60 px-6 py-8 text-center ring-1 ring-surface-border">
            <button
              type="button"
              onClick={() => (isRecordingThis ? stopRecording() : startRecording(task.id, task.max_seconds))}
              disabled={(!!recordingTaskId && !isRecordingThis) || !!recording || submitMutation.isPending}
              aria-label={isRecordingThis ? t("vizuMultilevel.recordStop") : t("vizuMultilevel.recordStart")}
              className={`flex h-16 w-16 items-center justify-center rounded-full text-white shadow-md transition-colors ${
                isRecordingThis ? "animate-pulse bg-danger" : "bg-gradient-to-br from-orange-600 to-orange-400"
              } disabled:cursor-not-allowed disabled:opacity-50`}
            >
              {isRecordingThis ? <Square size={22} /> : <Mic size={24} />}
            </button>

            <p className="text-sm font-semibold tabular-nums text-text-primary">
              {formatClock(isRecordingThis ? elapsed : (recording?.duration ?? 0))}
            </p>

            <p className="text-sm text-text-secondary">
              {isRecordingThis && t("vizuMultilevel.recording")}
              {!isRecordingThis && recording && t("vizuMultilevel.recorded")}
              {!isRecordingThis && !recording && alreadySent && t("vizuMultilevel.recordedSent")}
              {!isRecordingThis && !recording && !alreadySent && t("vizuMultilevel.recordStart")}
            </p>

            {recording && (
              <>
                <audio controls src={recording.url} className="w-full max-w-sm" />
                <button
                  type="button"
                  onClick={() => discardRecording(task.id)}
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-accent-blue hover:underline"
                >
                  <RotateCcw size={14} />
                  {t("vizuMultilevel.reRecord")}
                </button>
              </>
            )}

            {micError && <p className="text-sm text-danger">{t("vizuMultilevel.micError")}</p>}
          </div>
        </div>
      )}

      {submitError && <p className="mt-4 text-sm font-medium text-orange-600">{submitError}</p>}

      <VizuMultilevelFinishConfirmDialog
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleSubmit}
        isSubmitting={submitMutation.isPending}
        blockedReason={canFinish ? null : t("vizuMultilevel.minRequiredError", { min: minRequired })}
      />
    </VizuMultilevelStepShell>
  );
}
