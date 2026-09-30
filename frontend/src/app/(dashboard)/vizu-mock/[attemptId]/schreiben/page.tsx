"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, CheckCircle2 } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMockFinishConfirmDialog from "@/features/vizu-mock/components/finish-confirm-dialog";
import VizuMockStepShell from "@/features/vizu-mock/components/step-shell";
import VizuMockWritingEditor from "@/features/vizu-mock/components/writing-editor";
import { getSkillMeta } from "@/features/vizu-mock/constants/skills";
import {
  getVizuMockSchreibenSubmissions,
  getVizuMockSchreibenTasks,
  saveVizuMockSchreibenDraft,
  submitVizuMockSchreiben,
} from "@/features/vizu-mock/services/vizu-mock-service";

/** Schreiben step — 5 real Aufgaben (1 per CEFR level), a plain-text
 * editor (no rich formatting, see writing-editor.tsx) with umlaut keys
 * and a word counter per Aufgabe. Drafts persist per Aufgabe ("Speichern"
 * + an implicit save on "Weiter" so a previous answer is never lost when
 * navigating back and forth); nothing is graded automatically — a
 * teacher grades every Aufgabe from the Teacher Panel afterward, so this
 * step never shows a CEFR level, only a submission confirmation. */
export default function VizuMockSchreibenPage() {
  const { t } = useTranslation();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("schreiben")!;
  const queryClient = useQueryClient();

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ["vizu-mock-schreiben-tasks"],
    queryFn: getVizuMockSchreibenTasks,
  });
  const { data: submissions, isLoading: submissionsLoading } = useQuery({
    queryKey: ["vizu-mock-schreiben-submissions", attemptId],
    queryFn: () => getVizuMockSchreibenSubmissions(attemptId),
  });

  const [taskIndex, setTaskIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [savedTaskIds, setSavedTaskIds] = useState<Record<string, boolean>>({});
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Resume previously-saved drafts exactly once, the instant the
  // submissions query first resolves — setState-during-render (React's
  // documented pattern for "adjust state when data arrives"), not an
  // effect, so there's no extra committed render in between.
  const [hydratedFrom, setHydratedFrom] = useState<typeof submissions>(undefined);
  if (submissions && submissions !== hydratedFrom) {
    const initial: Record<string, string> = {};
    const saved: Record<string, boolean> = {};
    for (const s of submissions) {
      initial[s.task_id] = s.content;
      saved[s.task_id] = true;
    }
    setAnswers(initial);
    setSavedTaskIds(saved);
    setHydratedFrom(submissions);
  }

  const saveMutation = useMutation({
    mutationFn: (taskId: string) => saveVizuMockSchreibenDraft(attemptId, taskId, answers[taskId] ?? ""),
    onSuccess: (_, taskId) => {
      setSavedTaskIds((prev) => ({ ...prev, [taskId]: true }));
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-schreiben-submissions", attemptId] });
    },
  });

  const submitMutation = useMutation({
    mutationFn: () => submitVizuMockSchreiben(attemptId),
    onSuccess: () => {
      setSubmitted(true);
      setConfirmOpen(false);
    },
  });

  const task = tasks?.[taskIndex];
  const isLastTask = tasks ? taskIndex === tasks.length - 1 : false;

  function updateAnswer(taskId: string, content: string) {
    setAnswers((prev) => ({ ...prev, [taskId]: content }));
    setSavedTaskIds((prev) => ({ ...prev, [taskId]: false }));
  }

  async function handleNext() {
    if (task) await saveMutation.mutateAsync(task.id);
    setTaskIndex((i) => i + 1);
  }

  async function handlePrevious() {
    if (task) await saveMutation.mutateAsync(task.id);
    setTaskIndex((i) => Math.max(0, i - 1));
  }

  if (tasksLoading || submissionsLoading || !tasks) {
    return (
      <VizuMockStepShell skill={skill} footer={null}>
        <p className="py-10 text-center text-sm text-text-secondary">{t("common.loading")}</p>
      </VizuMockStepShell>
    );
  }

  if (submitted) {
    return <VizuMockSchreibenSuccessView attemptId={attemptId} />;
  }

  return (
    <VizuMockStepShell
      skill={skill}
      onFinishClick={() => setConfirmOpen(true)}
      footer={
        <div className="flex items-center gap-2">
          {taskIndex > 0 && (
            <Button variant="secondary" onClick={handlePrevious} disabled={saveMutation.isPending}>
              <ArrowLeft size={16} />
              {t("vizuMock.previous")}
            </Button>
          )}
          {task && (
            <Button
              variant="secondary"
              onClick={() => saveMutation.mutate(task.id)}
              disabled={saveMutation.isPending}
            >
              {savedTaskIds[task.id] && !saveMutation.isPending ? (
                <>
                  <Check size={16} /> {t("vizuMock.schreibenSaved")}
                </>
              ) : (
                t("vizuMock.schreibenSave")
              )}
            </Button>
          )}
          <Button
            onClick={() => (isLastTask ? setConfirmOpen(true) : handleNext())}
            disabled={saveMutation.isPending}
          >
            {isLastTask ? t("vizuMock.schreibenAbsenden") : t("vizuMock.next")}
          </Button>
        </div>
      }
    >
      {task && (
        <div className="space-y-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {t("vizuMock.aufgabeStep", { current: taskIndex + 1, total: tasks.length })}
          </p>

          <div>
            <h2 className="mb-2 text-base font-bold text-text-primary">{task.title}</h2>
            <div className="whitespace-pre-line rounded-2xl bg-surface-hover/60 p-4 text-sm leading-relaxed text-text-secondary ring-1 ring-surface-border">
              {task.instruction}
            </div>
          </div>

          {task.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={task.image_url} alt="" className="w-full rounded-2xl object-cover" />
          )}

          <div>
            <label className="mb-1.5 block text-sm font-semibold text-text-primary">
              {t("vizuMock.writingAnswerLabel")}
            </label>
            <VizuMockWritingEditor
              value={answers[task.id] ?? ""}
              onChange={(content) => updateAnswer(task.id, content)}
              minWords={task.min_words}
              maxWords={task.max_words}
            />
          </div>
        </div>
      )}

      <VizuMockFinishConfirmDialog
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => submitMutation.mutate()}
        isSubmitting={submitMutation.isPending}
      />
    </VizuMockStepShell>
  );
}

function VizuMockSchreibenSuccessView({ attemptId }: { attemptId: string }) {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-lg space-y-6 text-center">
      <div className="rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-8 text-white shadow-[var(--shadow-lg)]">
        <CheckCircle2 size={36} className="mx-auto mb-3" />
        <p className="text-base font-bold">{t("vizuMock.schreibenSubmittedTitle")}</p>
      </div>

      <div className="flex justify-center">
        <Link href={`/vizu-mock/${attemptId}/sprechen`}>
          <Button>
            {t("vizuMock.continueToSprechen")}
            <ArrowRight size={16} />
          </Button>
        </Link>
      </div>
    </div>
  );
}
