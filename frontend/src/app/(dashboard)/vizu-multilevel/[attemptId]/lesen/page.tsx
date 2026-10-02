"use client";

import { useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

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

/** Lesen step. One screen per Aufgabe (reading text + its questions). The
 * 20-minute window is owned by the server (see use-section.ts); finishing —
 * by the last Aufgabe, the always-visible "Testni yakunlash" button, or the
 * timer expiring — submits whatever is answered (unanswered = 0 points) and
 * moves straight on to Hören. No CEFR level and no score is shown here. */
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
  const [taskIndex, setTaskIndex] = useState(0);
  const [finishConfirmOpen, setFinishConfirmOpen] = useState(false);
  const [submitFailed, setSubmitFailed] = useState(false);
  const submittingRef = useRef(false);

  const submitMutation = useMutation({
    mutationFn: () => {
      const payload = (tasks ?? []).flatMap((task) =>
        task.questions.map((q) => ({ question_id: q.id, option_id: answers[q.id] ?? null })),
      );
      return submitVizuMultilevelLesen(attemptId, payload);
    },
    onSuccess: () => {
      clear();
      router.push(nextStepPath(attemptId, "lesen"));
    },
    onError: (error) => {
      // 409 = already submitted / out of order: the flow gate sends the
      // student to the right step. Anything else: let them retry.
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

  return (
    <VizuMultilevelStepShell
      skill={skill}
      initialSeconds={gate.secondsRemaining}
      onTimerExpire={handleSubmit}
      onFinishClick={() => setFinishConfirmOpen(true)}
      footer={
        <Button
          onClick={() => (!task || isLastTask ? handleSubmit() : setTaskIndex((i) => i + 1))}
          disabled={submitMutation.isPending}
        >
          {submitMutation.isPending
            ? t("common.loading")
            : !task || isLastTask
              ? t("vizuMultilevel.finishLesen")
              : t("vizuMultilevel.next")}
        </Button>
      }
    >
      {!task ? (
        <SectionPreparing skill="lesen" />
      ) : (
        <div className="space-y-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {t("vizuMultilevel.aufgabeStep", { current: taskIndex + 1, total: tasks.length })}
          </p>

          {task.passage_text && <VizuMultilevelPassage text={task.passage_text} />}

          <VizuMultilevelQuestionList questions={task.questions} answers={answers} onSelect={select} showQuestionPassage />
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
