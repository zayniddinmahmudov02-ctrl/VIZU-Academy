"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowRight } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import VizuMultilevelQuestionList, { VizuMultilevelPassage } from "@/features/vizu-multilevel/components/question-list";
import { SectionError, SectionLoading, SectionPreparing } from "@/features/vizu-multilevel/components/section-states";
import VizuMultilevelStepShell from "@/features/vizu-multilevel/components/step-shell";
import { getSkillMeta, nextStepPath } from "@/features/vizu-multilevel/constants/skills";
import { isConflict, useVizuMultilevelSection } from "@/features/vizu-multilevel/hooks/use-section";
import { usePersistedAnswers } from "@/features/vizu-multilevel/hooks/use-persisted-answers";
import { getVizuMultilevelLesenTasks, submitVizuMultilevelLesen } from "@/features/vizu-multilevel/services/vizu-multilevel-service";
import type { VizuMultilevelLesenResult } from "@/features/vizu-multilevel/types/vizu-multilevel.types";

/** Lesen step: the 20 questions are shown one at a time as "Test 1 / 20 …
 * Test 20 / 20", each with the text it belongs to. The CEFR level of a
 * question is never sent to or shown to the student. Finishing — on the
 * last question, via the always-visible "Testni yakunlash" button, or when
 * the server-owned 20-minute window ends — grades on the server
 * (unanswered = 0) and shows the Lesen Ergebnis before moving on. */
export default function VizuMultilevelLesenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("lesen")!;

  const gate = useVizuMultilevelSection(attemptId, "lesen");
  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-multilevel-lesen-tasks"],
    queryFn: getVizuMultilevelLesenTasks,
  });

  const { answers, select, clear } = usePersistedAnswers(attemptId, "lesen");
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<VizuMultilevelLesenResult | null>(null);
  const [finishConfirmOpen, setFinishConfirmOpen] = useState(false);
  const [submitFailed, setSubmitFailed] = useState(false);
  const submittingRef = useRef(false);

  // Questions 1..20 in order, each carrying its text.
  const items = useMemo(
    () => (tasks ?? []).flatMap((task) => task.questions.map((question) => ({ passage: task.passage_text, question }))),
    [tasks],
  );

  const submitMutation = useMutation({
    mutationFn: () =>
      submitVizuMultilevelLesen(
        attemptId,
        items.map(({ question }) => ({ question_id: question.id, option_id: answers[question.id] ?? null })),
      ),
    onSuccess: (data) => {
      clear();
      setResult(data);
    },
    onError: (error) => {
      if (isConflict(error)) {
        router.push(nextStepPath(attemptId, "lesen"));
        return;
      }
      submittingRef.current = false;
      setSubmitFailed(true);
    },
  });

  function handleSubmit() {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setSubmitFailed(false);
    submitMutation.mutate();
  }

  if (result) {
    return <LesenResultView attemptId={attemptId} result={result} />;
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

  const current = items[index];
  const isLast = index >= items.length - 1;
  const total = items.length;

  return (
    <VizuMultilevelStepShell
      skill={skill}
      initialSeconds={gate.secondsRemaining}
      onTimerExpire={handleSubmit}
      onFinishClick={() => setFinishConfirmOpen(true)}
      footer={
        <Button
          onClick={() => (!current || isLast ? handleSubmit() : setIndex((i) => i + 1))}
          disabled={submitMutation.isPending}
        >
          {submitMutation.isPending
            ? t("common.loading")
            : !current || isLast
              ? t("vizuMultilevel.finishLesen")
              : t("vizuMultilevel.next")}
        </Button>
      }
    >
      {!current ? (
        <SectionPreparing skill="lesen" />
      ) : (
        <div className="space-y-5">
          <div>
            <div className="mb-2 flex items-center justify-between text-xs font-semibold text-text-muted">
              <span className="uppercase tracking-wide">{t("vizuMultilevel.testOf", { current: index + 1, total })}</span>
              <span>{Math.round(((index + 1) / total) * 100)}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-surface-border" role="progressbar" aria-valuenow={index + 1} aria-valuemin={1} aria-valuemax={total}>
              <div className="h-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all" style={{ width: `${((index + 1) / total) * 100}%` }} />
            </div>
          </div>

          {current.passage && <VizuMultilevelPassage text={current.passage} />}

          <VizuMultilevelQuestionList
            key={current.question.id}
            questions={[current.question]}
            answers={answers}
            onSelect={select}
            showQuestionPassage
            hideNumbers
          />
        </div>
      )}

      {submitFailed && <p className="mt-4 text-sm text-danger">{t("vizuMultilevel.submitFailed")}</p>}

      <VizuMultilevelFinishConfirmDialog
        open={finishConfirmOpen}
        onCancel={() => setFinishConfirmOpen(false)}
        onConfirm={() => {
          setFinishConfirmOpen(false);
          handleSubmit();
        }}
        isSubmitting={submitMutation.isPending}
      />
    </VizuMultilevelStepShell>
  );
}

function LesenResultView({ attemptId, result }: { attemptId: string; result: VizuMultilevelLesenResult }) {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-center text-xl font-bold text-text-primary">{t("vizuMultilevel.lesenResultTitle")}</h1>

      <div className="rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{t("vizuMultilevel.points")}</p>
        <p className="mt-1 text-4xl font-extrabold text-text-primary">
          {result.total_points} / {result.max_points}
        </p>

        <p className="mt-6 text-xs font-semibold uppercase tracking-wide text-text-muted">
          {t("vizuMultilevel.determinedLevel")}
        </p>
        <p className="mt-1 text-4xl font-extrabold text-accent-blue">{result.lesen_level ?? "—"}</p>

        {result.below_a1 && (
          <div className="mt-5 flex items-start justify-center gap-2 rounded-xl bg-warning/10 px-4 py-3 text-left text-sm text-warning">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            {t("vizuMultilevel.lesenBelowA1")}
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <Stat label={t("vizuMultilevel.statCorrect")} value={result.correct} />
        <Stat label={t("vizuMultilevel.statWrong")} value={result.wrong} />
        <Stat label={t("vizuMultilevel.statUnanswered")} value={result.unanswered} />
      </div>

      <div className="flex justify-center">
        <Link href={nextStepPath(attemptId, "lesen")}>
          <Button>
            {t("vizuMultilevel.continueNext")}
            <ArrowRight size={16} />
          </Button>
        </Link>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl bg-surface-card p-4 ring-1 ring-surface-border">
      <p className="text-2xl font-bold text-text-primary">{value}</p>
      <p className="mt-0.5 text-xs text-text-muted">{label}</p>
    </div>
  );
}
