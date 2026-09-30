"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Mic, RotateCcw, Square } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMockFinishConfirmDialog from "@/features/vizu-mock/components/finish-confirm-dialog";
import VizuMockStepShell from "@/features/vizu-mock/components/step-shell";
import { getSkillMeta } from "@/features/vizu-mock/constants/skills";

type RecordState = "idle" | "recording" | "recorded";

/** Sprechen step — timer, progress, a task placeholder and a recording
 * UI shell (start/stop/re-record). No microphone is actually captured
 * and nothing is uploaded: there's no real task/grading to attach audio
 * to yet (per spec) — this is the visual/interaction shell a later phase
 * wires to the real MediaRecorder + upload flow (same pattern the
 * lesson-player's real Sprechen recorder already uses elsewhere). */
export default function VizuMockSprechenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("sprechen")!;

  const [state, setState] = useState<RecordState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [finishConfirmOpen, setFinishConfirmOpen] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  function startRecording() {
    setElapsed(0);
    setState("recording");
    intervalRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
  }

  function stopRecording() {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setState("recorded");
  }

  function reRecord() {
    setElapsed(0);
    setState("idle");
  }

  function handleFinish() {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setFinishConfirmOpen(false);
    router.push(`/vizu-mock/${attemptId}/natijalar`);
  }

  const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const ss = String(elapsed % 60).padStart(2, "0");

  return (
    <VizuMockStepShell
      skill={skill}
      onFinishClick={() => setFinishConfirmOpen(true)}
      footer={
        <Button
          disabled={state !== "recorded"}
          onClick={() => router.push(`/vizu-mock/${attemptId}/natijalar`)}
        >
          {t("vizuMock.submit")}
        </Button>
      }
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3 rounded-2xl bg-surface-hover/60 p-4 ring-1 ring-surface-border">
          <Mic size={18} className="mt-0.5 shrink-0 text-text-muted" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              {t("vizuMock.speakingPrompt")}
            </p>
            <p className="mt-1 text-sm text-text-secondary">{t("vizuMock.speakingPromptPlaceholder")}</p>
          </div>
        </div>

        <div className="flex flex-col items-center gap-4 rounded-2xl bg-surface-hover/60 px-6 py-10 text-center ring-1 ring-surface-border">
          <button
            type="button"
            onClick={state === "recording" ? stopRecording : startRecording}
            disabled={state === "recorded"}
            aria-label={state === "recording" ? t("vizuMock.recordStop") : t("vizuMock.recordStart")}
            className={`flex h-16 w-16 items-center justify-center rounded-full text-white shadow-md transition-colors ${
              state === "recording" ? "bg-danger animate-pulse" : "bg-gradient-to-br from-orange-600 to-orange-400"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            {state === "recording" ? <Square size={22} /> : <Mic size={24} />}
          </button>

          <p className="text-sm font-semibold text-text-primary tabular-nums">
            {mm}:{ss}
          </p>

          <p className="text-sm text-text-secondary">
            {state === "idle" && t("vizuMock.recordStart")}
            {state === "recording" && t("vizuMock.recording")}
            {state === "recorded" && t("vizuMock.recorded")}
          </p>

          {state === "recorded" && (
            <button
              type="button"
              onClick={reRecord}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-accent-blue hover:underline"
            >
              <RotateCcw size={14} />
              {t("vizuMock.reRecord")}
            </button>
          )}
        </div>
      </div>

      <VizuMockFinishConfirmDialog
        open={finishConfirmOpen}
        onCancel={() => setFinishConfirmOpen(false)}
        onConfirm={handleFinish}
      />
    </VizuMockStepShell>
  );
}
