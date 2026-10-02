"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, ArrowLeft, ArrowRight } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import VizuMultilevelProgressHeader from "@/features/vizu-multilevel/components/progress-header";
import VizuMultilevelQuestionList, { VizuMultilevelPassage } from "@/features/vizu-multilevel/components/question-list";
import { SectionError, SectionLoading, SectionPreparing } from "@/features/vizu-multilevel/components/section-states";
import VizuMultilevelStepShell from "@/features/vizu-multilevel/components/step-shell";
import { getSkillMeta, nextStepPath } from "@/features/vizu-multilevel/constants/skills";
import {
  apiErrorCode,
  isConflict,
  minAnswersRequired,
  useVizuMultilevelSection,
} from "@/features/vizu-multilevel/hooks/use-section";
import { usePersistedAnswers } from "@/features/vizu-multilevel/hooks/use-persisted-answers";
import { getVizuMultilevelLesenTasks, submitVizuMultilevelLesen } from "@/features/vizu-multilevel/services/vizu-multilevel-service";
import type { VizuMultilevelLesenResult } from "@/features/vizu-multilevel/types/vizu-multilevel.types";

/** Lesen step: one question per screen ("Aufgabe n / 20") with its text,
 * free back/forward navigation, answers kept while navigating (and across a
 * reload), and a progress bar of answered questions. At least 5 questions
 * must be answered before Lesen can be submitted (enforced by the server;
 * the only exception is the time running out). No CEFR level and no correct
 * answer is ever shown during the test. */
export default function VizuMultilevelLesenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("lesen")!;

  const gate = useVizuMultilevelSection(attemptId, "lesen");
  const { data: tasks, isLoading, isError } = useQuery({
    queryKey: ["vizu-multilevel-lesen-tasks"],
    queryFn: getVizuMultilevelLesenTasks,
  });

  const { answers, select, clear } = usePersistedAnswers(attemptId, "lesen");
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [result, setResult] = useState<VizuMultilevelLesenResult | null>(null);
  const [finishConfirmOpen, setFinishConfirmOpen] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const submittingRef = useRef(false);

  // Questions 1..20 in order, each carrying its text and Aufgabe number.
  const items = useMemo(
    () =>
      (tasks ?? []).flatMap((task) =>
        task.questions.map((question) => ({ aufgabe: task.order_index, passage: task.passage_text, question })),
      ),
    [tasks],
  );
  const answeredCount = items.filter(({ question }) => answers[question.id]).length;
  const minRequired = minAnswersRequired(items.length);
  const canFinish = answeredCount >= minRequired;

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
      submittingRef.current = false;
      const code = apiErrorCode(error);
      if (code === "MIN_ANSWERS_REQUIRED") {
        setSubmitError(t("vizuMultilevel.minRequiredError", { min: minRequired }));
        return;
      }
      if (isConflict(error)) {
        router.push(nextStepPath(attemptId, "lesen"));
        return;
      }
      setSubmitError(t("vizuMultilevel.submitFailed"));
    },
  });

  function handleSubmit() {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setSubmitError(null);
    submitMutation.mutate();
  }

  function go(next: number) {
    setDirection(next > index ? 1 : -1);
    setIndex(next);
  }

  if (result) {
    return <LesenResultView attemptId={attemptId} result={result} />;
  }

  if (gate.status === "error" || isError) {
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
        <div className="flex items-center gap-2">
          {current && index > 0 && (
            <Button variant="secondary" onClick={() => go(index - 1)} disabled={submitMutation.isPending}>
              <ArrowLeft size={16} />
              {t("vizuMultilevel.previous")}
            </Button>
          )}
          <Button
            onClick={() => (!current || isLast ? handleSubmit() : go(index + 1))}
            disabled={submitMutation.isPending || ((!current || isLast) && !canFinish)}
          >
            {submitMutation.isPending
              ? t("common.loading")
              : !current || isLast
                ? t("vizuMultilevel.finishLesen")
                : t("vizuMultilevel.next")}
            {current && !isLast && <ArrowRight size={16} />}
          </Button>
        </div>
      }
    >
      {!current ? (
        <SectionPreparing skill="lesen" />
      ) : (
        <div className="space-y-5">
          <VizuMultilevelProgressHeader
            positionLabel={t("vizuMultilevel.aufgabePos", { current: index + 1, total })}
            answered={answeredCount}
            total={total}
            minRequired={minRequired}
          />

          <AnimatePresence mode="wait" initial={false} custom={direction}>
            <motion.div
              key={current.question.id}
              custom={direction}
              initial={{ opacity: 0, x: direction * 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: direction * -24 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="space-y-5"
            >
              <p className="text-sm font-extrabold uppercase tracking-wide text-slate-900 dark:text-white">
                {t("vizuMultilevel.aufgabe", { number: current.aufgabe })}
              </p>

              {current.passage && <VizuMultilevelPassage text={current.passage} />}

              <VizuMultilevelQuestionList
                questions={[current.question]}
                answers={answers}
                onSelect={select}
                showQuestionPassage
                numberFromOrder
                showLetters
              />
            </motion.div>
          </AnimatePresence>
        </div>
      )}

      {submitError && <p className="mt-4 text-sm font-medium text-orange-600">{submitError}</p>}

      <VizuMultilevelFinishConfirmDialog
        open={finishConfirmOpen}
        onCancel={() => setFinishConfirmOpen(false)}
        onConfirm={() => {
          setFinishConfirmOpen(false);
          handleSubmit();
        }}
        isSubmitting={submitMutation.isPending}
        blockedReason={canFinish ? null : t("vizuMultilevel.minRequiredError", { min: minRequired })}
      />
    </VizuMultilevelStepShell>
  );
}

function LesenResultView({ attemptId, result }: { attemptId: string; result: VizuMultilevelLesenResult }) {
  const { t } = useTranslation();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="mx-auto max-w-2xl space-y-6"
    >
      <h1 className="text-center text-xl font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.lesenResultTitle")}</h1>

      <div className="rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{t("vizuMultilevel.points")}</p>
        <p className="mt-1 text-4xl font-extrabold text-slate-900 dark:text-white">
          {result.total_points} / {result.max_points}
        </p>

        <p className="mt-6 text-xs font-semibold uppercase tracking-wide text-text-muted">{t("vizuMultilevel.determinedLevel")}</p>
        <p className="mt-1 text-4xl font-extrabold text-blue-600">{result.lesen_level ?? "—"}</p>

        {result.below_a1 && (
          <div className="mt-5 flex items-start justify-center gap-2 rounded-xl bg-orange-50 px-4 py-3 text-left text-sm text-orange-700 dark:bg-orange-500/10 dark:text-orange-300">
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
    </motion.div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl bg-surface-card p-4 ring-1 ring-surface-border">
      <p className="text-2xl font-bold text-slate-900 dark:text-white">{value}</p>
      <p className="mt-0.5 text-xs text-text-muted">{label}</p>
    </div>
  );
}
