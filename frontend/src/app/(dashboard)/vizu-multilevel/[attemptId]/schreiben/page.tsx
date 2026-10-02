"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, Check, CircleDot, Send } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import SchreibenEvaluationFlow from "@/features/vizu-multilevel/components/schreiben-evaluation";
import { SectionError, SectionLoading, SectionPreparing } from "@/features/vizu-multilevel/components/section-states";
import VizuMultilevelStepShell from "@/features/vizu-multilevel/components/step-shell";
import VizuMultilevelWritingEditor from "@/features/vizu-multilevel/components/writing-editor";
import { getSkillMeta, nextStepPath } from "@/features/vizu-multilevel/constants/skills";
import {
  apiErrorCode,
  isConflict,
  useVizuMultilevelSectionOrSubmitted,
} from "@/features/vizu-multilevel/hooks/use-section";
import {
  getVizuMultilevelSchreibenSubmissions,
  getVizuMultilevelSchreibenTasks,
  saveVizuMultilevelSchreibenDraft,
  submitVizuMultilevelSchreiben,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";

type Phase = "write" | "evaluating";

/** Schreiben: 5 Aufgaben in a split screen — instructions on the left, the
 * editor on the right. Every Aufgabe is saved to the server on its own
 * ("Antwort speichern & weiter"), so nothing is lost when navigating or reloading,
 * and stays editable until the final submission. "Alle 5 Aufgaben abgeben"
 * needs all five saved (the server enforces it too), locks the answers and
 * starts the server-side evaluation; the student then sees the evaluation
 * screen (>= 10 s, until the real result exists) and the detailed result.
 * No CEFR level is shown while writing. */
export default function VizuMultilevelSchreibenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("schreiben")!;

  const gate = useVizuMultilevelSectionOrSubmitted(attemptId, "schreiben");
  const tasksQuery = useQuery({ queryKey: ["vizu-multilevel-schreiben-tasks"], queryFn: getVizuMultilevelSchreibenTasks });
  const subsQuery = useQuery({
    queryKey: ["vizu-multilevel-schreiben-submissions", attemptId],
    queryFn: () => getVizuMultilevelSchreibenSubmissions(attemptId),
  });
  const tasks = tasksQuery.data;

  const [taskIndex, setTaskIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  // Text as last CONFIRMED by the server — the single source of truth for "Gespeichert".
  const [saved, setSaved] = useState<Record<string, string>>({});
  const [phase, setPhase] = useState<Phase>("write");
  const [justSubmitted, setJustSubmitted] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submittingRef = useRef(false);

  // Restore the server-side drafts once they arrive (setState during render).
  const [hydratedFrom, setHydratedFrom] = useState<typeof subsQuery.data>(undefined);
  if (subsQuery.data && subsQuery.data !== hydratedFrom) {
    const fromServer: Record<string, string> = {};
    for (const s of subsQuery.data) fromServer[s.task_id] = s.content;
    setAnswers((prev) => ({ ...fromServer, ...prev }));
    setSaved(fromServer);
    setHydratedFrom(subsQuery.data);
  }

  const dirty = (tasks ?? []).some((task) => (answers[task.id] ?? "") !== (saved[task.id] ?? ""));
  useEffect(() => {
    if (!dirty || phase !== "write") return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, phase]);

  const saveMutation = useMutation({
    mutationFn: ({ taskId, content }: { taskId: string; content: string }) =>
      saveVizuMultilevelSchreibenDraft(attemptId, taskId, content),
    onSuccess: (submission) => {
      setSaved((prev) => ({ ...prev, [submission.task_id]: submission.content }));
      setError(null);
    },
    onError: () => setError(t("vizuMultilevel.saveFailed")),
  });

  const submitMutation = useMutation({
    mutationFn: async () => {
      const current = tasks?.[taskIndex];
      if (current && (answers[current.id] ?? "") !== (saved[current.id] ?? "")) {
        try {
          await saveVizuMultilevelSchreibenDraft(attemptId, current.id, answers[current.id] ?? "");
        } catch {
          /* time up — the server keeps the last in-time drafts */
        }
      }
      await submitVizuMultilevelSchreiben(attemptId);
    },
    onSuccess: () => {
      setJustSubmitted(true);
      setPhase("evaluating");
    },
    onError: (e) => {
      submittingRef.current = false;
      const code = apiErrorCode(e);
      if (code === "MIN_ANSWERS_REQUIRED") setError(t("vizuMultilevel.allTasksRequiredError"));
      else if (code === "SECTION_ALREADY_SUBMITTED") setPhase("evaluating");
      else if (isConflict(e)) router.push(nextStepPath(attemptId, "schreiben"));
      else setError(t("vizuMultilevel.submitFailed"));
    },
  });

  function handleSubmit() {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setError(null);
    setConfirmOpen(false);
    submitMutation.mutate();
  }

  async function saveCurrent(): Promise<boolean> {
    const task = tasks?.[taskIndex];
    if (!task) return true;
    const content = answers[task.id] ?? "";
    if (content === (saved[task.id] ?? "")) return true;
    try {
      await saveMutation.mutateAsync({ taskId: task.id, content });
      return true;
    } catch {
      return false;
    }
  }

  async function goTo(index: number) {
    if (await saveCurrent()) setTaskIndex(index);
  }

  // ---- after submission (fresh, or on reload) ----
  if (phase === "evaluating" || gate.status === "submitted") {
    return (
      <SchreibenEvaluationFlow
        attemptId={attemptId}
        minDurationMs={justSubmitted ? 10_000 : 0}
        onContinue={() => router.push(nextStepPath(attemptId, "schreiben"))}
      />
    );
  }

  if (gate.status === "error" || tasksQuery.isError || subsQuery.isError) {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionError />
      </VizuMultilevelStepShell>
    );
  }
  if (gate.status === "loading" || !tasks || subsQuery.isLoading) {
    return (
      <VizuMultilevelStepShell skill={skill} footer={null}>
        <SectionLoading />
      </VizuMultilevelStepShell>
    );
  }

  const task = tasks[taskIndex];
  const isLast = taskIndex >= tasks.length - 1;
  const completeCount = tasks.filter((x) => (saved[x.id] ?? "").trim()).length;
  const allComplete = tasks.length > 0 && completeCount === tasks.length;
  const currentSaved = task ? (answers[task.id] ?? "") === (saved[task.id] ?? "") : true;

  return (
    <VizuMultilevelStepShell
      skill={skill}
      wide
      initialSeconds={gate.secondsRemaining}
      onTimerExpire={handleSubmit}
      footer={
        <div className="flex flex-wrap items-center justify-end gap-2">
          {task && taskIndex > 0 && (
            <Button variant="secondary" onClick={() => void goTo(taskIndex - 1)} disabled={saveMutation.isPending}>
              <ArrowLeft size={16} />
              {t("vizuMultilevel.previous")}
            </Button>
          )}
          {task && (
            <Button
              variant="secondary"
              onClick={() => void (isLast ? saveCurrent() : goTo(taskIndex + 1))}
              disabled={saveMutation.isPending || submitMutation.isPending}
            >
              {isLast ? t("vizuMultilevel.schreibenSave") : t("vizuMultilevel.saveAndNext")}
            </Button>
          )}
          <Button
            onClick={() => (allComplete || !task ? setConfirmOpen(true) : setError(t("vizuMultilevel.allTasksRequiredError")))}
            disabled={submitMutation.isPending || (!!task && !allComplete)}
          >
            <Send size={15} />
            {submitMutation.isPending ? t("common.loading") : t("vizuMultilevel.submitAll", { count: tasks.length })}
          </Button>
        </div>
      }
    >
      {!task ? (
        <SectionPreparing skill="schreiben" />
      ) : (
        <div className="space-y-5">
          {/* Aufgabe navigation */}
          <div className="flex flex-wrap items-center gap-2" role="tablist">
            {tasks.map((x, i) => {
              const isSaved = (saved[x.id] ?? "").trim() !== "" && (answers[x.id] ?? "") === (saved[x.id] ?? "");
              return (
                <motion.button
                  key={x.id}
                  type="button"
                  role="tab"
                  aria-selected={i === taskIndex}
                  whileTap={{ scale: 0.96 }}
                  onClick={() => void goTo(i)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-bold ring-1 transition-colors",
                    i === taskIndex
                      ? "bg-blue-600 text-white ring-blue-600"
                      : "bg-surface-card text-slate-700 ring-slate-200 hover:ring-blue-300 dark:text-slate-200 dark:ring-slate-700",
                  )}
                >
                  {isSaved ? <Check size={13} className={i === taskIndex ? "text-white" : "text-emerald-600"} /> : <CircleDot size={12} className="text-orange-500" />}
                  {t("vizuMultilevel.aufgabe", { number: x.order_index })}
                </motion.button>
              );
            })}
            <span className="ml-auto text-xs font-semibold text-slate-500 dark:text-slate-400">
              {t("vizuMultilevel.savedOf", { done: completeCount, total: tasks.length })}
            </span>
          </div>

          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={task.id}
              initial={{ opacity: 0, x: 18 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -18 }}
              transition={{ duration: 0.18 }}
              className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]"
            >
              {/* LEFT: task */}
              <section className="rounded-2xl bg-slate-50 p-5 ring-1 ring-slate-200 dark:bg-slate-800/60 dark:ring-slate-700">
                <p className="text-xs font-extrabold uppercase tracking-wide text-blue-600">
                  {t("vizuMultilevel.schreibenAufgabeOf", { number: task.order_index, total: tasks.length })}
                </p>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{t("vizuMultilevel.thema")}</p>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">{task.title}</h2>
                <div className="mt-4 whitespace-pre-line text-sm leading-relaxed text-slate-700 dark:text-slate-200">{task.instruction}</div>
                {task.image_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={task.image_url} alt="" className="mt-4 w-full rounded-xl object-cover" />
                )}
                <p className="mt-5 inline-flex rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-700 dark:bg-orange-500/15 dark:text-orange-300">
                  {t("vizuMultilevel.wordTarget", { min: task.min_words, max: task.max_words })}
                </p>
              </section>

              {/* RIGHT: editor */}
              <section className="rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-sm font-semibold text-slate-900 dark:text-white">{t("vizuMultilevel.writingAnswerLabel")}</label>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 text-xs font-semibold",
                      saveMutation.isPending ? "text-slate-500" : currentSaved && (saved[task.id] ?? "") ? "text-emerald-600" : "text-orange-600",
                    )}
                    aria-live="polite"
                  >
                    {saveMutation.isPending ? (
                      t("vizuMultilevel.saving")
                    ) : currentSaved && (saved[task.id] ?? "") ? (
                      <>
                        <Check size={13} /> {t("vizuMultilevel.schreibenSaved")}
                      </>
                    ) : (
                      t("vizuMultilevel.unsaved")
                    )}
                  </span>
                </div>
                <VizuMultilevelWritingEditor
                  value={answers[task.id] ?? ""}
                  onChange={(content) => setAnswers((prev) => ({ ...prev, [task.id]: content }))}
                  minWords={task.min_words}
                  maxWords={task.max_words}
                />
              </section>
            </motion.div>
          </AnimatePresence>
        </div>
      )}

      {error && <p className="mt-4 text-sm font-medium text-orange-600">{error}</p>}

      <VizuMultilevelFinishConfirmDialog
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleSubmit}
        isSubmitting={submitMutation.isPending}
        title={t("vizuMultilevel.submitAllConfirm", { count: tasks.length })}
        body={t("vizuMultilevel.submitAllBody")}
        confirmLabel={t("vizuMultilevel.submitAllConfirmButton")}
      />
    </VizuMultilevelStepShell>
  );
}
