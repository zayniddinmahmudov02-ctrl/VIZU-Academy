"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowRight, Check, X } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMockStepShell from "@/features/vizu-mock/components/step-shell";
import { getSkillMeta } from "@/features/vizu-mock/constants/skills";
import { getVizuMockLesenTasks, submitVizuMockLesen } from "@/features/vizu-mock/services/vizu-mock-service";
import type { VizuMockLesenResult } from "@/features/vizu-mock/types/vizu-mock.types";

/** Lesen step — 10 real Aufgaben (2 per CEFR level), one screen per
 * Aufgabe with its passage(s) and 2 questions. A single 20-minute timer
 * covers the whole module (see step-shell.tsx); when it expires, or the
 * student finishes Aufgabe 10, whatever's answered so far is submitted
 * and graded server-side — nothing is graded client-side. */
export default function VizuMockLesenPage() {
  const { t } = useTranslation();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("lesen")!;

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-mock-lesen-tasks"],
    queryFn: getVizuMockLesenTasks,
  });

  const [taskIndex, setTaskIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<VizuMockLesenResult | null>(null);
  const [timedOut, setTimedOut] = useState(false);
  const submittingRef = useRef(false);

  const submitMutation = useMutation({
    mutationFn: () => {
      const payload = (tasks ?? []).flatMap((task) =>
        task.questions.map((q) => ({ question_id: q.id, option_id: answers[q.id] ?? null })),
      );
      return submitVizuMockLesen(attemptId, payload);
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
    return <VizuMockLesenResultView attemptId={attemptId} result={result} timedOut={timedOut} />;
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
              ? t("vizuMock.finishLesen")
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
            <span className="rounded-full bg-accent-blue/10 px-2.5 py-1 text-xs font-bold text-accent-blue">
              {task.level}
            </span>
          </div>

          {task.passage_text && (
            <div className="rounded-2xl bg-surface-hover/60 p-4 text-sm leading-relaxed text-text-secondary ring-1 ring-surface-border sm:p-5">
              {task.passage_text.split("\n").map((line, i) => (
                <p key={i} className={i > 0 ? "mt-2" : undefined}>
                  {line}
                </p>
              ))}
            </div>
          )}

          <div className="space-y-6">
            {task.questions.map((question, qi) => (
              <div key={question.id}>
                <p className="mb-2 text-sm font-semibold text-text-primary">
                  {t("vizuMock.question", { number: qi + 1 })}
                </p>

                {question.passage_text && (
                  <div className="mb-3 rounded-2xl bg-surface-hover/60 p-4 text-sm leading-relaxed text-text-secondary ring-1 ring-surface-border">
                    {question.passage_text.split("\n").map((line, i) => (
                      <p key={i} className={i > 0 ? "mt-2" : undefined}>
                        {line}
                      </p>
                    ))}
                  </div>
                )}

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

function VizuMockLesenResultView({
  attemptId,
  result,
  timedOut,
}: {
  attemptId: string;
  result: VizuMockLesenResult;
  timedOut: boolean;
}) {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-center text-xl font-bold text-text-primary">{t("vizuMock.lesenResultTitle")}</h1>

      {timedOut && (
        <div className="flex items-center gap-2 rounded-xl bg-warning/10 px-4 py-3 text-sm text-warning">
          <AlertCircle size={16} />
          {t("vizuMock.lesenTimeUpNote")}
        </div>
      )}

      <div className="overflow-hidden rounded-2xl ring-1 ring-surface-border">
        <table className="w-full text-left text-sm">
          <tbody className="divide-y divide-surface-border">
            {result.level_scores.map((entry) => (
              <tr key={entry.level} className="bg-surface-card">
                <td className="flex items-center gap-2 px-4 py-3 font-semibold text-text-primary">
                  {entry.passed ? (
                    <Check size={15} className="text-success" />
                  ) : (
                    <X size={15} className="text-text-muted" />
                  )}
                  {entry.level}
                </td>
                <td className="px-4 py-3 text-right text-text-secondary">
                  {entry.points}/{entry.max_points}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-8 text-center text-white shadow-[var(--shadow-lg)]">
        <p className="text-sm font-semibold uppercase tracking-wide text-white/70">{t("vizuMock.lesenNiveau")}</p>
        <p className="mt-2 text-4xl font-extrabold">{result.lesen_level ?? "—"}</p>
        {!result.lesen_level && <p className="mt-2 text-sm text-white/70">{t("vizuMock.lesenNiveauNotConfirmed")}</p>}
        <p className="mt-4 text-sm text-white/80">
          {t("vizuMock.points")}: {result.total_points}/{result.max_points}
        </p>
      </div>

      <div className="flex justify-center">
        <Link href={`/vizu-mock/${attemptId}/hoeren`}>
          <Button>
            {t("vizuMock.continueToHoeren")}
            <ArrowRight size={16} />
          </Button>
        </Link>
      </div>
    </div>
  );
}
