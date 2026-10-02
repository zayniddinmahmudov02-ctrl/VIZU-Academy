"use client";

import { useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import { SectionError, SectionLoading, SectionPreparing } from "@/features/vizu-multilevel/components/section-states";
import VizuMultilevelStepShell from "@/features/vizu-multilevel/components/step-shell";
import VizuMultilevelWritingEditor from "@/features/vizu-multilevel/components/writing-editor";
import { getSkillMeta, nextStepPath } from "@/features/vizu-multilevel/constants/skills";
import VizuMultilevelProgressHeader from "@/features/vizu-multilevel/components/progress-header";
import {
  apiErrorCode,
  isConflict,
  minAnswersRequired,
  useVizuMultilevelSection,
} from "@/features/vizu-multilevel/hooks/use-section";
import {
  getVizuMultilevelSchreibenSubmissions,
  getVizuMultilevelSchreibenTasks,
  saveVizuMultilevelSchreibenDraft,
  submitVizuMultilevelSchreiben,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";

/** Schreiben step. A plain-text editor (no rich formatting) with umlaut
 * keys and a word counter per Aufgabe. Drafts persist on the server per
 * Aufgabe ("Speichern" + an implicit save on "Weiter"/finish) — but only
 * while the server-owned 20-minute window is open. Nothing is graded
 * automatically (a teacher grades afterwards), so this step never shows a
 * level or score; finishing moves straight on to Sprechen. */
export default function VizuMultilevelSchreibenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("schreiben")!;
  const queryClient = useQueryClient();

  const gate = useVizuMultilevelSection(attemptId, "schreiben");
  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ["vizu-multilevel-schreiben-tasks"],
    queryFn: getVizuMultilevelSchreibenTasks,
  });
  const { data: submissions, isLoading: submissionsLoading } = useQuery({
    queryKey: ["vizu-multilevel-schreiben-submissions", attemptId],
    queryFn: () => getVizuMultilevelSchreibenSubmissions(attemptId),
  });

  const [taskIndex, setTaskIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [savedTaskIds, setSavedTaskIds] = useState<Record<string, boolean>>({});
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const submittingRef = useRef(false);

  // Resume previously-saved drafts exactly once, the instant the
  // submissions query first resolves (setState-during-render: React's
  // documented pattern for "adjust state when data arrives").
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
    mutationFn: (taskId: string) => saveVizuMultilevelSchreibenDraft(attemptId, taskId, answers[taskId] ?? ""),
    onSuccess: (_, taskId) => {
      setSavedTaskIds((prev) => ({ ...prev, [taskId]: true }));
      queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-schreiben-submissions", attemptId] });
    },
  });

  const submitMutation = useMutation({
    mutationFn: async () => {
      // Best-effort save of the Aufgabe on screen. After the deadline the
      // server rejects it (409) — the final submit below still goes through.
      const current = tasks?.[taskIndex];
      if (current && answers[current.id] && !savedTaskIds[current.id]) {
        try {
          await saveVizuMultilevelSchreibenDraft(attemptId, current.id, answers[current.id]);
        } catch {
          /* window closed or transient — submit regardless */
        }
      }
      await submitVizuMultilevelSchreiben(attemptId);
    },
    onSuccess: () => router.push(nextStepPath(attemptId, "schreiben")),
    onError: (error) => {
      if (apiErrorCode(error) === "MIN_ANSWERS_REQUIRED") {
        submittingRef.current = false;
        setSubmitError(t("vizuMultilevel.minRequiredError", { min: minRequired }));
        return;
      }
      if (isConflict(error)) {
        router.push(nextStepPath(attemptId, "schreiben"));
        return;
      }
      submittingRef.current = false;
      setSubmitError(t("vizuMultilevel.submitFailed"));
    },
  });

  function handleSubmit() {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setSubmitError(null);
    setConfirmOpen(false);
    submitMutation.mutate();
  }

  const task = tasks?.[taskIndex];
  const isLastTask = tasks ? taskIndex >= tasks.length - 1 : false;
  const writtenCount = (tasks ?? []).filter((x) => (answers[x.id] ?? "").trim()).length;
  const minRequired = minAnswersRequired(tasks?.length ?? 0);
  const canFinish = writtenCount >= minRequired;

  function updateAnswer(taskId: string, content: string) {
    setAnswers((prev) => ({ ...prev, [taskId]: content }));
    setSavedTaskIds((prev) => ({ ...prev, [taskId]: false }));
  }

  async function goTo(index: number) {
    if (task && !savedTaskIds[task.id] && answers[task.id]) {
      try {
        await saveMutation.mutateAsync(task.id);
      } catch {
        /* keep the text locally; the student can retry with "Speichern" */
      }
    }
    setTaskIndex(index);
  }

  if (gate.status === "error") {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionError />
      </VizuMultilevelStepShell>
    );
  }
  if (gate.status === "loading" || tasksLoading || submissionsLoading || !tasks) {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionLoading />
      </VizuMultilevelStepShell>
    );
  }

  return (
    <VizuMultilevelStepShell
      skill={skill}
      initialSeconds={gate.secondsRemaining}
      onTimerExpire={handleSubmit}
      onFinishClick={() => setConfirmOpen(true)}
      footer={
        <div className="flex flex-wrap items-center justify-end gap-2">
          {task && taskIndex > 0 && (
            <Button variant="secondary" onClick={() => goTo(taskIndex - 1)} disabled={saveMutation.isPending}>
              <ArrowLeft size={16} />
              {t("vizuMultilevel.previous")}
            </Button>
          )}
          {task && (
            <Button variant="secondary" onClick={() => saveMutation.mutate(task.id)} disabled={saveMutation.isPending}>
              {savedTaskIds[task.id] && !saveMutation.isPending ? (
                <>
                  <Check size={16} /> {t("vizuMultilevel.schreibenSaved")}
                </>
              ) : (
                t("vizuMultilevel.schreibenSave")
              )}
            </Button>
          )}
          <Button
            onClick={() => (!task || isLastTask ? setConfirmOpen(true) : goTo(taskIndex + 1))}
            disabled={saveMutation.isPending || submitMutation.isPending}
          >
            {!task || isLastTask ? t("vizuMultilevel.schreibenAbsenden") : t("vizuMultilevel.next")}
          </Button>
        </div>
      }
    >
      {!task ? (
        <SectionPreparing skill="schreiben" />
      ) : (
        <div className="space-y-6">
          <VizuMultilevelProgressHeader
            positionLabel={t("vizuMultilevel.aufgabePos", { current: taskIndex + 1, total: tasks.length })}
            answered={writtenCount}
            total={tasks.length}
            minRequired={minRequired}
          />

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
              {t("vizuMultilevel.writingAnswerLabel")}
            </label>
            <VizuMultilevelWritingEditor
              value={answers[task.id] ?? ""}
              onChange={(content) => updateAnswer(task.id, content)}
              minWords={task.min_words}
              maxWords={task.max_words}
            />
          </div>

          {saveMutation.isError && <p className="text-sm text-danger">{t("vizuMultilevel.saveFailed")}</p>}
        </div>
      )}

      {submitError && <p className="mt-4 text-sm font-medium text-orange-600">{submitError}</p>}

      <VizuMultilevelFinishConfirmDialog
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleSubmit}
        isSubmitting={submitMutation.isPending}
        blockedReason={canFinish ? null : t("vizuMultilevel.minRequiredError", { min: minRequired })}
      />
    </VizuMultilevelStepShell>
  );
}
