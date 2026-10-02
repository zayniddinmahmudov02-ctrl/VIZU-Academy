"use client";

import { useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Headphones } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import VizuMultilevelQuestionList from "@/features/vizu-multilevel/components/question-list";
import { SectionError, SectionLoading, SectionPreparing } from "@/features/vizu-multilevel/components/section-states";
import VizuMultilevelStepShell from "@/features/vizu-multilevel/components/step-shell";
import { getSkillMeta, nextStepPath } from "@/features/vizu-multilevel/constants/skills";
import { isConflict, useVizuMultilevelSection } from "@/features/vizu-multilevel/hooks/use-section";
import { usePersistedAnswers } from "@/features/vizu-multilevel/hooks/use-persisted-answers";
import { getVizuMultilevelHoerenTasks, submitVizuMultilevelHoeren } from "@/features/vizu-multilevel/services/vizu-multilevel-service";

/** Hören step. One screen per Aufgabe (audio player + its questions). The
 * 20-minute window is owned by the server; finishing — by the last Aufgabe,
 * "Testni yakunlash", or the timer expiring — submits whatever is answered
 * (unanswered = 0 points) and moves straight on to Schreiben. No CEFR
 * level, score or transcript is ever shown or sent to the student. */
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

  const { answers, select, clear } = usePersistedAnswers(attemptId, "hoeren");
  const [taskIndex, setTaskIndex] = useState(0);
  const [finishConfirmOpen, setFinishConfirmOpen] = useState(false);
  const [submitFailed, setSubmitFailed] = useState(false);
  const submittingRef = useRef(false);

  const submitMutation = useMutation({
    mutationFn: () => {
      const payload = (tasks ?? []).flatMap((task) =>
        task.questions.map((q) => ({ question_id: q.id, option_id: answers[q.id] ?? null })),
      );
      return submitVizuMultilevelHoeren(attemptId, payload);
    },
    onSuccess: () => {
      clear();
      router.push(nextStepPath(attemptId, "hoeren"));
    },
    onError: (error) => {
      if (isConflict(error)) {
        router.push(nextStepPath(attemptId, "hoeren"));
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
              ? t("vizuMultilevel.finishHoeren")
              : t("vizuMultilevel.next")}
        </Button>
      }
    >
      {!task ? (
        <SectionPreparing skill="hoeren" />
      ) : (
        <div className="space-y-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {t("vizuMultilevel.aufgabeStep", { current: taskIndex + 1, total: tasks.length })}
          </p>

          <div className="flex flex-col items-center gap-3 rounded-2xl bg-surface-hover/60 px-6 py-8 text-center ring-1 ring-surface-border">
            <Headphones size={26} className="text-accent-blue" />
            {task.audio_url ? (
              <audio key={task.id} controls src={task.audio_url} className="w-full max-w-sm" />
            ) : (
              <p className="text-sm text-text-muted">{t("vizuMultilevel.audioMissing")}</p>
            )}
            <p className="text-xs text-text-muted">{t("vizuMultilevel.listeningInstruction")}</p>
          </div>

          <VizuMultilevelQuestionList questions={task.questions} answers={answers} onSelect={select} />
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
