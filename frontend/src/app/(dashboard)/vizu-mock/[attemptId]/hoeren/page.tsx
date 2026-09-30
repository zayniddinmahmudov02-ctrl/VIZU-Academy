"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowRight, Headphones } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMockStepShell from "@/features/vizu-mock/components/step-shell";
import { getSkillMeta } from "@/features/vizu-mock/constants/skills";
import { getVizuMockHoerenTasks, submitVizuMockHoeren } from "@/features/vizu-mock/services/vizu-mock-service";
import type { VizuMockHoerenResult } from "@/features/vizu-mock/types/vizu-mock.types";

/** Hören step — 5 real Aufgaben (1 per CEFR level), one screen per
 * Aufgabe with its audio player and 4 questions. A single 20-minute
 * timer covers the whole module (see step-shell.tsx); when it expires,
 * or the student finishes Aufgabe 5, whatever's answered so far is
 * submitted and graded server-side. No CEFR level is ever shown here —
 * only the raw score — the audio script/transcript is never sent to the
 * client at all (see hoeren_service.list_hoeren_tasks on the backend). */
export default function VizuMockHoerenPage() {
  const { t } = useTranslation();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("hoeren")!;

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-mock-hoeren-tasks"],
    queryFn: getVizuMockHoerenTasks,
  });

  const [taskIndex, setTaskIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<VizuMockHoerenResult | null>(null);
  const [timedOut, setTimedOut] = useState(false);
  const submittingRef = useRef(false);

  const submitMutation = useMutation({
    mutationFn: () => {
      const payload = (tasks ?? []).flatMap((task) =>
        task.questions.map((q) => ({ question_id: q.id, option_id: answers[q.id] ?? null })),
      );
      return submitVizuMockHoeren(attemptId, payload);
    },
    onSuccess: (data) => setResult(data),
  });

  function handleSubmit(dueToTimeout: boolean) {
    if (submittingRef.current || result) return;
    submittingRef.current = true;
    if (dueToTimeout) setTimedOut(true);
    submitMutation.mutate();
  }

  const task = tasks?.[taskIndex];
  const isLastTask = tasks ? taskIndex === tasks.length - 1 : false;

  if (isLoading || !tasks) {
    return (
      <VizuMockStepShell skill={skill} footer={null}>
        <p className="py-10 text-center text-sm text-text-secondary">{t("common.loading")}</p>
      </VizuMockStepShell>
    );
  }

  if (result) {
    return <VizuMockHoerenResultView attemptId={attemptId} result={result} timedOut={timedOut} />;
  }

  return (
    <VizuMockStepShell
      skill={skill}
      onTimerExpire={() => handleSubmit(true)}
      footer={
        <Button
          onClick={() => (isLastTask ? handleSubmit(false) : setTaskIndex((i) => i + 1))}
          disabled={submitMutation.isPending}
        >
          {submitMutation.isPending
            ? t("common.loading")
            : isLastTask
              ? t("vizuMock.finishHoeren")
              : t("vizuMock.next")}
        </Button>
      }
    >
      {task && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              {t("vizuMock.aufgabeStep", { current: taskIndex + 1, total: tasks.length })}
            </p>
          </div>

          <div className="flex flex-col items-center gap-3 rounded-2xl bg-surface-hover/60 px-6 py-8 text-center ring-1 ring-surface-border">
            <Headphones size={26} className="text-accent-blue" />
            {task.audio_url ? (
              <audio key={task.id} controls src={task.audio_url} className="w-full max-w-sm" />
            ) : (
              <p className="text-sm text-text-muted">{t("vizuMock.placeholderNote")}</p>
            )}
            <p className="text-xs text-text-muted">{t("vizuMock.listeningInstruction")}</p>
          </div>

          <div className="space-y-6">
            {task.questions.map((question, qi) => (
              <div key={question.id}>
                <p className="mb-2 text-sm font-semibold text-text-primary">
                  {t("vizuMock.question", { number: qi + 1 })}
                </p>

                <p className="mb-3 text-sm text-text-primary">{question.prompt}</p>

                <div className="space-y-2">
                  {question.options.map((option) => {
                    const selected = answers[question.id] === option.id;
                    return (
                      <button
                        key={option.id}
                        type="button"
                        onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: option.id }))}
                        className={`w-full rounded-xl px-4 py-3 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                          selected
                            ? "bg-accent-blue/10 text-text-primary ring-accent-blue/40"
                            : "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30"
                        }`}
                      >
                        {option.option_text}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </VizuMockStepShell>
  );
}

function VizuMockHoerenResultView({
  attemptId,
  result,
  timedOut,
}: {
  attemptId: string;
  result: VizuMockHoerenResult;
  timedOut: boolean;
}) {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-center text-xl font-bold text-text-primary">{t("vizuMock.hoerenResultTitle")}</h1>

      {timedOut && (
        <div className="flex items-center gap-2 rounded-xl bg-warning/10 px-4 py-3 text-sm text-warning">
          <AlertCircle size={16} />
          {t("vizuMock.lesenTimeUpNote")}
        </div>
      )}

      {/* No CEFR level is shown here by design — only the score. */}
      <div className="rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-8 text-center text-white shadow-[var(--shadow-lg)]">
        <p className="text-sm font-semibold uppercase tracking-wide text-white/70">{t("vizuMock.points")}</p>
        <p className="mt-2 text-4xl font-extrabold">
          {result.total_points}/{result.max_points}
        </p>
      </div>

      <div className="flex justify-center">
        <Link href={`/vizu-mock/${attemptId}/schreiben`}>
          <Button>
            {t("vizuMock.continueToSchreiben")}
            <ArrowRight size={16} />
          </Button>
        </Link>
      </div>
    </div>
  );
}
