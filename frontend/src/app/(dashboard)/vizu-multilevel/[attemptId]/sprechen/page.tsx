"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Check, CheckCircle2, Clock, Lightbulb, Loader2, Lock, Mic, RefreshCw, RotateCcw, Save, Send, Square } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import { SectionError, SectionLoading, SectionPreparing } from "@/features/vizu-multilevel/components/section-states";
import SprechenEvaluationFlow from "@/features/vizu-multilevel/components/sprechen-evaluation";
import SprechenWaveform from "@/features/vizu-multilevel/components/sprechen-waveform";
import VizuMultilevelStepShell from "@/features/vizu-multilevel/components/step-shell";
import { getSkillMeta, nextStepPath } from "@/features/vizu-multilevel/constants/skills";
import { apiErrorCode, isConflict, useVizuMultilevelSectionOrSubmitted } from "@/features/vizu-multilevel/hooks/use-section";
import { useSprechenRecorder } from "@/features/vizu-multilevel/hooks/use-sprechen-recorder";
import {
  getVizuMultilevelAttemptSprechenTasks,
  getVizuMultilevelSprechenSubmissions,
  retryVizuMultilevelSprechenEvaluation,
  submitVizuMultilevelSprechen,
  uploadVizuMultilevelSprechenRecording,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";
import type {
  VizuMultilevelSpeakingStatus,
  VizuMultilevelSpeakingSubmission,
  VizuMultilevelSpeakingTask,
} from "@/features/vizu-multilevel/types/vizu-multilevel.types";

type Phase = "test" | "evaluating";

const IN_FLIGHT: (VizuMultilevelSpeakingStatus | null)[] = ["PROCESSING", "TRANSCRIBED", "EVALUATING"];

function clock(totalSeconds: number): string {
  const s = Math.max(0, totalSeconds);
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

/** Sprechen: 5 Aufgaben, one at a time. LEFT = Aufgabe, RIGHT = microphone /
 * recording / playback / processing status. Every answer is recorded in the
 * browser (re-recordable until saved), saved ONCE with "Antwort speichern"
 * (the server keeps it — refresh-safe — and starts speech-to-text + AI
 * evaluation in the background), then the next Aufgabe opens. No level or
 * score is shown during the test; after "Sprechen abschließen" the
 * processing screen (>= 10 s, until the real result exists) and the result
 * follow. */
export default function VizuMultilevelSprechenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("sprechen")!;

  const gate = useVizuMultilevelSectionOrSubmitted(attemptId, "sprechen");
  const tasksQuery = useQuery({
    queryKey: ["vizu-multilevel-sprechen-tasks", attemptId],
    queryFn: () => getVizuMultilevelAttemptSprechenTasks(attemptId),
  });
  const subsKey = ["vizu-multilevel-sprechen-submissions", attemptId];
  const subsQuery = useQuery({
    queryKey: subsKey,
    queryFn: () => getVizuMultilevelSprechenSubmissions(attemptId),
    refetchInterval: (query) => (query.state.data?.some((s) => IN_FLIGHT.includes(s.status)) ? 3000 : false),
  });

  const tasks = tasksQuery.data;
  const subs = subsQuery.data ?? [];
  const savedByTask = new Map<string, VizuMultilevelSpeakingSubmission>(subs.map((s) => [s.task_id, s]));
  const firstOpen = tasks ? tasks.findIndex((task) => !savedByTask.has(task.id)) : -1;

  const [selected, setSelected] = useState<number | null>(null);
  const [phase, setPhase] = useState<Phase>("test");
  const [justSubmitted, setJustSubmitted] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recorder = useSprechenRecorder();

  const saveMutation = useMutation({
    mutationFn: ({ task }: { task: VizuMultilevelSpeakingTask }) =>
      uploadVizuMultilevelSprechenRecording(attemptId, task.id, recorder.answer!.blob, recorder.answer!.duration),
    onSuccess: async () => {
      setError(null);
      recorder.reset();
      setSelected(null); // jump to the next open Aufgabe
      await queryClient.invalidateQueries({ queryKey: subsKey });
    },
    onError: async (e) => {
      const code = apiErrorCode(e);
      if (code === "ANSWER_ALREADY_SAVED" || code === "PREVIOUS_TASK_REQUIRED") {
        recorder.reset();
        setSelected(null);
        await queryClient.invalidateQueries({ queryKey: subsKey });
        return;
      }
      if (code === "SECTION_TIME_UP" || code === "SECTION_ALREADY_SUBMITTED") {
        setPhase("evaluating");
        return;
      }
      setError(t("vizuMultilevel.spSaveFailed"));
    },
  });

  const retryMutation = useMutation({
    mutationFn: () => retryVizuMultilevelSprechenEvaluation(attemptId),
    onSettled: () => void queryClient.invalidateQueries({ queryKey: subsKey }),
  });

  const submitMutation = useMutation({
    mutationFn: () => submitVizuMultilevelSprechen(attemptId),
    onSuccess: () => {
      setJustSubmitted(true);
      setPhase("evaluating");
    },
    onError: (e) => {
      const code = apiErrorCode(e);
      if (code === "MIN_ANSWERS_REQUIRED") setError(t("vizuMultilevel.spAllRequired", { count: tasks?.length ?? 5 }));
      else if (isConflict(e)) setPhase("evaluating");
      else setError(t("vizuMultilevel.submitFailed"));
    },
  });

  function finish() {
    recorder.stop();
    setConfirmOpen(false);
    submitMutation.mutate();
  }

  // ---- after the final submit (fresh, or on reload) ----
  if (phase === "evaluating" || gate.status === "submitted") {
    return (
      <VizuMultilevelStepShell skill={skill} wide footer={null}>
        <SprechenEvaluationFlow
          attemptId={attemptId}
          minDurationMs={justSubmitted ? 10_000 : 0}
          onContinue={() => router.push(nextStepPath(attemptId, "sprechen"))}
        />
      </VizuMultilevelStepShell>
    );
  }
  if (gate.status === "error" || tasksQuery.isError || subsQuery.isError) {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionError />
      </VizuMultilevelStepShell>
    );
  }
  if (gate.status === "loading" || !tasks || subsQuery.isLoading) {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionLoading />
      </VizuMultilevelStepShell>
    );
  }
  if (tasks.length === 0) {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionPreparing skill="sprechen" />
      </VizuMultilevelStepShell>
    );
  }

  const allSaved = firstOpen === -1;
  const index = selected ?? (allSaved ? tasks.length - 1 : firstOpen);
  const task = tasks[index];
  const saved = savedByTask.get(task.id);
  const locked = !saved && index !== firstOpen;
  const busy = recorder.status === "recording" || recorder.status === "requesting" || saveMutation.isPending;
  const remaining = task.max_seconds - recorder.elapsed;
  const tooShort = recorder.answer !== null && task.min_seconds > 0 && recorder.answer.duration < task.min_seconds;

  function select(i: number) {
    if (busy) return;
    if (i !== index) recorder.reset();
    setError(null);
    setSelected(i);
  }

  return (
    <VizuMultilevelStepShell
      skill={skill}
      wide
      initialSeconds={gate.secondsRemaining}
      onTimerExpire={finish}
      footer={
        <div className="flex flex-wrap items-center justify-end gap-2">
          {saved && !allSaved && index !== firstOpen && (
            <Button variant="secondary" onClick={() => select(firstOpen)} disabled={busy}>
              {t("vizuMultilevel.spNext", { number: tasks[firstOpen].order_index })}
            </Button>
          )}
          <Button
            onClick={() => (allSaved ? setConfirmOpen(true) : setError(t("vizuMultilevel.spAllRequired", { count: tasks.length })))}
            disabled={!allSaved || busy || submitMutation.isPending}
          >
            <Send size={15} />
            {submitMutation.isPending ? t("common.loading") : t("vizuMultilevel.spFinish")}
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        {/* Aufgabe navigation (sequential) */}
        <div className="flex flex-wrap items-center gap-2" role="tablist">
          {tasks.map((x, i) => {
            const isSaved = savedByTask.has(x.id);
            const isLocked = !isSaved && i !== firstOpen;
            return (
              <button
                key={x.id}
                type="button"
                role="tab"
                aria-selected={i === index}
                disabled={isLocked || busy}
                onClick={() => select(i)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-bold ring-1 transition-colors disabled:cursor-not-allowed",
                  i === index
                    ? "bg-blue-600 text-white ring-blue-600"
                    : "bg-surface-card text-slate-700 ring-slate-200 hover:ring-blue-300 dark:text-slate-200 dark:ring-slate-700",
                  isLocked && i !== index && "opacity-50",
                )}
              >
                {isSaved ? (
                  <Check size={13} className={i === index ? "text-white" : "text-emerald-600"} />
                ) : isLocked ? (
                  <Lock size={11} />
                ) : (
                  <Mic size={12} className={i === index ? "text-white" : "text-orange-500"} />
                )}
                {t("vizuMultilevel.aufgabe", { number: x.order_index })}
              </button>
            );
          })}
          <span className="ml-auto text-xs font-semibold text-slate-500 dark:text-slate-400">
            {t("vizuMultilevel.spSavedOf", { done: savedByTask.size, total: tasks.length })}
          </span>
        </div>

        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={task.id}
            initial={{ opacity: 0, x: 18 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -18 }}
            transition={{ duration: 0.18 }}
            className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]"
          >
            {/* LEFT: Aufgabe */}
            <section className="rounded-2xl bg-slate-50 p-5 ring-1 ring-slate-200 dark:bg-slate-800/60 dark:ring-slate-700" data-testid="sprechen-task">
              <p className="text-xs font-extrabold uppercase tracking-wide text-blue-600">
                {t("vizuMultilevel.spAufgabeOf", { number: task.order_index, total: tasks.length })}
              </p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{t("vizuMultilevel.spThema")}</p>
              <h2 className="text-lg font-bold text-[#0f2a4a] dark:text-white">{task.title}</h2>
              <p className="mt-4 whitespace-pre-line text-[15px] leading-relaxed text-slate-800 dark:text-slate-100">{task.instruction}</p>
              {task.preparation_text && (
                <div className="mt-4 flex gap-2 rounded-xl bg-white p-3 text-sm text-slate-600 ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-700">
                  <Lightbulb size={16} className="mt-0.5 shrink-0 text-orange-500" />
                  <p>
                    <span className="font-semibold">{t("vizuMultilevel.spHints")}: </span>
                    {task.preparation_text}
                  </p>
                </div>
              )}
              <p className="mt-5 inline-flex items-center gap-1.5 rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-700 dark:bg-orange-500/15 dark:text-orange-300">
                <Clock size={12} />
                {t("vizuMultilevel.spDuration", { min: task.min_seconds, max: task.max_seconds })}
              </p>
            </section>

            {/* RIGHT: microphone / recording / playback / status */}
            <section className="flex flex-col items-center gap-4 rounded-2xl bg-surface-card p-6 text-center shadow-[var(--shadow-sm)] ring-1 ring-surface-border" data-testid="sprechen-recorder">
              <p className="self-start text-sm font-semibold text-slate-900 dark:text-white">{t("vizuMultilevel.spAnswerTitle")}</p>

              {saved ? (
                <SavedState status={saved.status} onRetry={() => retryMutation.mutate()} retrying={retryMutation.isPending} />
              ) : locked ? (
                <p className="flex items-center gap-2 py-10 text-sm text-slate-500">
                  <Lock size={15} />
                  {t("vizuMultilevel.spLocked", { number: tasks[firstOpen]?.order_index ?? 1 })}
                </p>
              ) : (
                <>
                  <div className="relative mt-2 flex h-24 w-24 items-center justify-center">
                    {recorder.status === "recording" && (
                      <motion.span
                        className="absolute inset-0 rounded-full bg-red-500/20"
                        animate={{ scale: [1, 1.3, 1], opacity: [0.8, 0.2, 0.8] }}
                        transition={{ repeat: Infinity, duration: 1.6 }}
                      />
                    )}
                    <button
                      type="button"
                      data-testid="record-button"
                      onClick={() => (recorder.status === "recording" ? recorder.stop() : recorder.start(task.max_seconds))}
                      disabled={recorder.status === "requesting" || saveMutation.isPending || recorder.status === "recorded"}
                      aria-label={recorder.status === "recording" ? t("vizuMultilevel.recordStop") : t("vizuMultilevel.recordStart")}
                      className={cn(
                        "relative flex h-20 w-20 items-center justify-center rounded-full text-white shadow-lg transition-transform active:scale-95 disabled:cursor-not-allowed disabled:opacity-50",
                        recorder.status === "recording" ? "bg-red-600" : "bg-gradient-to-br from-blue-600 to-blue-500 hover:scale-105",
                      )}
                    >
                      {recorder.status === "recording" ? <Square size={26} /> : <Mic size={30} />}
                    </button>
                  </div>

                  <SprechenWaveform analyser={recorder.analyser} active={recorder.status === "recording"} />

                  <p className="text-2xl font-extrabold tabular-nums text-slate-900 dark:text-white" data-testid="record-clock">
                    {clock(recorder.status === "recorded" ? (recorder.answer?.duration ?? 0) : recorder.elapsed)}
                  </p>
                  <p className="-mt-2 text-xs font-medium text-slate-500" aria-live="polite">
                    {recorder.status === "recording" && (
                      <span className="inline-flex items-center gap-1.5 font-bold text-red-600">
                        <span className="h-2 w-2 animate-pulse rounded-full bg-red-600 motion-reduce:animate-none" />
                        {t("vizuMultilevel.recording")} · {t("vizuMultilevel.spRemaining", { time: clock(remaining) })}
                      </span>
                    )}
                    {recorder.status === "idle" && t("vizuMultilevel.spAutoStop", { seconds: task.max_seconds })}
                    {recorder.status === "recorded" && t("vizuMultilevel.recorded")}
                  </p>

                  {recorder.status === "denied" && (
                    <p role="alert" className="rounded-lg bg-orange-50 px-3 py-2 text-sm font-semibold text-orange-700 ring-1 ring-orange-200">
                      {t("vizuMultilevel.spMicDenied")}
                    </p>
                  )}
                  {recorder.status === "unsupported" && (
                    <p role="alert" className="rounded-lg bg-orange-50 px-3 py-2 text-sm font-semibold text-orange-700 ring-1 ring-orange-200">
                      {t("vizuMultilevel.spMicUnsupported")}
                    </p>
                  )}

                  {recorder.answer && (
                    <div className="w-full space-y-3">
                      <audio controls src={recorder.answer.url} className="w-full" data-testid="playback" />
                      {tooShort && <p className="text-xs font-semibold text-orange-600">{t("vizuMultilevel.spTooShort", { seconds: task.min_seconds })}</p>}
                      <div className="flex flex-wrap justify-center gap-2">
                        <Button variant="secondary" onClick={recorder.reset} disabled={saveMutation.isPending}>
                          <RotateCcw size={15} />
                          {t("vizuMultilevel.spReRecord")}
                        </Button>
                        <Button onClick={() => saveMutation.mutate({ task })} disabled={saveMutation.isPending} data-testid="save-answer">
                          {saveMutation.isPending ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
                          {saveMutation.isPending ? t("vizuMultilevel.spUploading") : t("vizuMultilevel.spSave")}
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </section>
          </motion.div>
        </AnimatePresence>
      </div>

      {error && <p className="mt-4 text-sm font-medium text-orange-600">{error}</p>}

      <VizuMultilevelFinishConfirmDialog
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={finish}
        isSubmitting={submitMutation.isPending}
        title={t("vizuMultilevel.spFinishTitle")}
        body={t("vizuMultilevel.spFinishBody")}
        confirmLabel={t("vizuMultilevel.spFinish")}
      />
    </VizuMultilevelStepShell>
  );
}

/** A saved answer: never re-recordable; shows where the server pipeline is.
 * While processing nothing alarming is shown; a real failure offers a retry
 * (the recording itself is safe on the server). */
function SavedState({ status, onRetry, retrying }: { status: VizuMultilevelSpeakingStatus | null; onRetry: () => void; retrying: boolean }) {
  const { t } = useTranslation();
  if (status === "FAILED") {
    return (
      <div className="flex flex-col items-center gap-3 py-8" data-testid="answer-status">
        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{t("vizuMultilevel.spStatusFailed")}</p>
        <Button variant="secondary" onClick={onRetry} disabled={retrying}>
          <RefreshCw size={15} className={retrying ? "animate-spin" : ""} />
          {t("vizuMultilevel.spRetry")}
        </Button>
      </div>
    );
  }
  const processing = status === "PROCESSING" || status === "TRANSCRIBED" || status === "EVALUATING";
  return (
    <div className="flex flex-col items-center gap-3 py-8" data-testid="answer-status">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10">
        <CheckCircle2 size={34} className="text-emerald-600" />
      </div>
      <p className="text-sm font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.spStatusDone")}</p>
      {processing && (
        <p className="inline-flex items-center gap-1.5 text-xs text-slate-500">
          <Loader2 size={12} className="animate-spin" />
          {status === "PROCESSING" ? t("vizuMultilevel.spStatusTranscribing") : t("vizuMultilevel.spStatusAnalyzing")}
        </p>
      )}
      <p className="max-w-xs text-xs text-slate-500">{t("vizuMultilevel.spSaved")}</p>
    </div>
  );
}
