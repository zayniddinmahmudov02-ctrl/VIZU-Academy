"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, ArrowLeft, ArrowRight, Check } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMultilevelHoerenAudioPlayer from "@/features/vizu-multilevel/components/hoeren-audio-player";
import VizuMultilevelQuestionList from "@/features/vizu-multilevel/components/question-list";
import { SectionError, SectionLoading, SectionPreparing } from "@/features/vizu-multilevel/components/section-states";
import VizuMultilevelStepShell from "@/features/vizu-multilevel/components/step-shell";
import { getSkillMeta, nextStepPath } from "@/features/vizu-multilevel/constants/skills";
import {
  apiErrorCode,
  isConflict,
  minAnswersRequired,
  useVizuMultilevelSection,
} from "@/features/vizu-multilevel/hooks/use-section";
import VizuMultilevelProgressHeader from "@/features/vizu-multilevel/components/progress-header";
import {
  getVizuMultilevelHoerenDraft,
  getVizuMultilevelHoerenTasks,
  saveVizuMultilevelHoerenDraft,
  submitVizuMultilevelHoeren,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";
import type { VizuMultilevelHoerenResult } from "@/features/vizu-multilevel/types/vizu-multilevel.types";

type SaveState = "idle" | "saving" | "saved" | "error";

/** Hören step: five Aufgaben, one per page — the audio on top, the four
 * tests below. 20 tests x 1 point. Answers are autosaved to the server (a
 * refresh restores them); the final button grades on the server and locks
 * the answers. The 20 minutes are owned by the server and shared by all five
 * Aufgaben. No transcript, file name, path, level or correct answer ever
 * reaches this page. */
export default function VizuMultilevelHoerenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("hoeren")!;

  const gate = useVizuMultilevelSection(attemptId, "hoeren");
  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-multilevel-hoeren-tasks"],
    queryFn: getVizuMultilevelHoerenTasks,
  });
  const { data: draft } = useQuery({
    queryKey: ["vizu-multilevel-hoeren-draft", attemptId],
    queryFn: () => getVizuMultilevelHoerenDraft(attemptId),
    staleTime: Infinity,
    gcTime: 0,
    retry: false,
  });

  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [result, setResult] = useState<VizuMultilevelHoerenResult | null>(null);
  const [timedOut, setTimedOut] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const submittingRef = useRef(false);
  const pendingRef = useRef<Record<string, string>>({});
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Restore autosaved answers exactly once, when the draft first arrives.
  const [hydratedFrom, setHydratedFrom] = useState<typeof draft>(undefined);
  if (draft && draft !== hydratedFrom) {
    setAnswers((prev) => ({ ...draft, ...prev }));
    setHydratedFrom(draft);
  }

  const flush = useCallback(async () => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    const batch = pendingRef.current;
    const entries = Object.entries(batch);
    if (entries.length === 0) return;
    pendingRef.current = {};
    setSaveState("saving");
    try {
      await saveVizuMultilevelHoerenDraft(
        attemptId,
        entries.map(([question_id, option_id]) => ({ question_id, option_id })),
      );
      setSaveState("saved");
    } catch (error) {
      // Keep the unsaved answers so the next flush retries them. A 409
      // (time up / already submitted) is final — nothing more can be saved.
      if (!isConflict(error)) pendingRef.current = { ...batch, ...pendingRef.current };
      setSaveState("error");
    }
  }, [attemptId]);

  useEffect(
    () => () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    },
    [],
  );

  function select(questionId: string, optionId: string) {
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
    pendingRef.current[questionId] = optionId;
    setSaveState("idle");
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => void flush(), 600);
  }

  const allQuestions = (tasks ?? []).flatMap((task) => task.questions);
  const answeredCount = allQuestions.filter((q) => answers[q.id]).length;
  const minRequired = minAnswersRequired(allQuestions.length);
  const canFinish = answeredCount >= minRequired;

  const submitMutation = useMutation({
    mutationFn: async () => {
      await flush();
      return submitVizuMultilevelHoeren(
        attemptId,
        allQuestions.map((q) => ({ question_id: q.id, option_id: answers[q.id] ?? null })),
      );
    },
    onSuccess: (data) => setResult(data),
    onError: (error) => {
      submittingRef.current = false;
      if (apiErrorCode(error) === "MIN_ANSWERS_REQUIRED") {
        setSubmitError("required");
        return;
      }
      if (isConflict(error)) {
        router.push(nextStepPath(attemptId, "hoeren"));
        return;
      }
      setSubmitError("failed");
    },
  });

  function handleSubmit(dueToTimeout: boolean) {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setSubmitError(null);
    if (dueToTimeout) setTimedOut(true);
    submitMutation.mutate();
  }

  async function goTo(next: number) {
    await flush();
    setIndex(next);
  }

  if (result) {
    return <HoerenResultView attemptId={attemptId} result={result} timedOut={timedOut} />;
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

  const task = tasks[index];
  const isLast = index >= tasks.length - 1;

  return (
    <VizuMultilevelStepShell
      skill={skill}
      initialSeconds={gate.secondsRemaining}
      onTimerExpire={() => handleSubmit(true)}
      footer={
        <div className="flex flex-wrap items-center justify-end gap-2">
          {task && index > 0 && (
            <Button variant="secondary" onClick={() => void goTo(index - 1)} disabled={submitMutation.isPending}>
              <ArrowLeft size={16} />
              {t("vizuMultilevel.previous")}
            </Button>
          )}
          {task && (
            <Button variant="secondary" onClick={() => void flush()} disabled={submitMutation.isPending}>
              {saveState === "saved" ? (
                <>
                  <Check size={16} /> {t("vizuMultilevel.schreibenSaved")}
                </>
              ) : saveState === "saving" ? (
                t("common.loading")
              ) : (
                t("vizuMultilevel.saveAnswers")
              )}
            </Button>
          )}
          <Button
            onClick={() => (!task || isLast ? handleSubmit(false) : void goTo(index + 1))}
            disabled={submitMutation.isPending || (isLast && !canFinish)}
          >
            {submitMutation.isPending ? t("common.loading") : !task || isLast ? t("vizuMultilevel.finishHoeren") : t("vizuMultilevel.next")}
          </Button>
        </div>
      }
    >
      {!task ? (
        <SectionPreparing skill="hoeren" />
      ) : (
        <div className="space-y-6">
          <VizuMultilevelProgressHeader
            positionLabel={t("vizuMultilevel.aufgabeOf", { current: index + 1, total: tasks.length })}
            answered={answeredCount}
            total={allQuestions.length}
            minRequired={minRequired}
          />

          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={task.id}
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -24 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="space-y-6"
            >
              <VizuMultilevelHoerenAudioPlayer attemptId={attemptId} aufgabeNumber={task.order_index} hasAudio={task.has_audio} />

              <section className="rounded-2xl p-1">
                <h2 className="mb-4 text-xs font-bold uppercase tracking-wide text-text-muted">{t("vizuMultilevel.testsTitle")}</h2>
                <VizuMultilevelQuestionList
                  questions={task.questions}
                  answers={answers}
                  onSelect={select}
                  numberFromOrder
                  numberLabelKey="vizuMultilevel.testNumber"
                />
              </section>
            </motion.div>
          </AnimatePresence>

          {saveState === "error" && <p className="text-sm text-danger">{t("vizuMultilevel.saveFailed")}</p>}
        </div>
      )}

      {submitError === "required" && (
        <p className="mt-2 text-sm font-medium text-orange-600">{t("vizuMultilevel.minRequiredError", { min: minRequired })}</p>
      )}
      {submitError === "failed" && <p className="mt-2 text-sm text-danger">{t("vizuMultilevel.submitFailed")}</p>}
    </VizuMultilevelStepShell>
  );
}

function HoerenResultView({
  attemptId,
  result,
  timedOut,
}: {
  attemptId: string;
  result: VizuMultilevelHoerenResult;
  timedOut: boolean;
}) {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-center text-xl font-bold text-text-primary">{t("vizuMultilevel.hoerenResultTitle")}</h1>

      {timedOut && (
        <div className="flex items-center gap-2 rounded-xl bg-warning/10 px-4 py-3 text-sm text-warning">
          <AlertCircle size={16} />
          {t("vizuMultilevel.hoerenTimeUp")}
        </div>
      )}

      <div className="rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{t("vizuMultilevel.points")}</p>
        <p className="mt-1 text-4xl font-extrabold text-text-primary">
          {result.total_points} / {result.max_points}
        </p>
        <p className="mt-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
          {t("vizuMultilevel.determinedLevel")}:{" "}
          <span className="text-lg font-extrabold text-blue-600">{result.hoeren_level ?? t("vizuMultilevel.belowA1")}</span>
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <Stat label={t("vizuMultilevel.statCorrect")} value={result.correct} />
        <Stat label={t("vizuMultilevel.statWrong")} value={result.wrong} />
        <Stat label={t("vizuMultilevel.statUnanswered")} value={result.unanswered} />
      </div>

      <div className="flex justify-center">
        <Link href={nextStepPath(attemptId, "hoeren")}>
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
