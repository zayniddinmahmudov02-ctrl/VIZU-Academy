"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, animate, motion, useReducedMotion } from "framer-motion";
import { AlertCircle, ArrowRight, CheckCircle2, ChevronDown, Lightbulb, Mic, RefreshCw, TrendingUp } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { getVizuMultilevelSprechenEvaluation, retryVizuMultilevelSprechenEvaluation } from "../services/vizu-multilevel-service";
import type { VizuMultilevelSpeakingEvaluation, VizuMultilevelSpeakingTaskEvaluation } from "../types/vizu-multilevel.types";

const STEP_KEYS = [
  "vizuMultilevel.spStepUpload",
  "vizuMultilevel.spStepDetect",
  "vizuMultilevel.spStepTranscribe",
  "vizuMultilevel.spStepAnalyze",
  "vizuMultilevel.spStepResult",
];

/** After "Sprechen abschließen": a processing screen for at least
 * `minDurationMs` (10 s after a fresh submission) that stays until the
 * server reports the REAL result — never a faked score. FAILED (e.g. the AI
 * provider is temporarily unavailable) offers a retry. */
export default function SprechenEvaluationFlow({
  attemptId,
  minDurationMs,
  onContinue,
}: {
  attemptId: string;
  minDurationMs: number;
  onContinue: () => void;
}) {
  const { t } = useTranslation();
  const [minElapsed, setMinElapsed] = useState(minDurationMs <= 0);

  useEffect(() => {
    if (minDurationMs <= 0) return;
    const timer = setTimeout(() => setMinElapsed(true), minDurationMs);
    return () => clearTimeout(timer);
  }, [minDurationMs]);

  const evaluation = useQuery({
    queryKey: ["vizu-multilevel-sprechen-evaluation", attemptId],
    queryFn: () => getVizuMultilevelSprechenEvaluation(attemptId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "DONE" || status === "FAILED" ? false : 2500;
    },
  });
  const retry = useMutation({
    mutationFn: () => retryVizuMultilevelSprechenEvaluation(attemptId),
    onSettled: () => void evaluation.refetch(),
  });

  const data = evaluation.data;
  if (data?.status === "DONE" && minElapsed) return <SprechenResult data={data} onContinue={onContinue} />;
  if ((data?.status === "FAILED" || evaluation.isError) && minElapsed && !retry.isPending) {
    return (
      <div className="mx-auto max-w-md rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <AlertCircle size={30} className="mx-auto text-orange-500" />
        <p className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">{t("vizuMultilevel.spEvalFailed")}</p>
        <Button className="mt-4" onClick={() => retry.mutate()}>
          <RefreshCw size={15} />
          {t("vizuMultilevel.spRetry")}
        </Button>
      </div>
    );
  }
  return <ProcessingScreen evaluated={data?.evaluated ?? 0} total={data?.total_tasks ?? 5} />;
}

function ProcessingScreen({ evaluated, total }: { evaluated: number; total: number }) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const [step, setStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setStep((s) => Math.min(s + 1, STEP_KEYS.length - 1)), 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      data-testid="sprechen-processing"
      className="mx-auto flex min-h-[440px] max-w-xl flex-col items-center justify-center rounded-card bg-surface-card p-10 text-center shadow-[var(--shadow-lg)] ring-1 ring-surface-border"
    >
      <div className="relative flex h-20 w-20 items-center justify-center">
        <motion.span
          className="absolute inset-0 rounded-full bg-blue-500/15"
          animate={reduce ? undefined : { scale: [1, 1.35, 1], opacity: [0.7, 0, 0.7] }}
          transition={{ repeat: Infinity, duration: 2 }}
        />
        <motion.div
          animate={reduce ? undefined : { rotate: 360 }}
          transition={{ repeat: Infinity, duration: 2.4, ease: "linear" }}
          className="absolute inset-0 rounded-full border-4 border-blue-100 border-t-orange-500"
        />
        <Mic size={26} className="text-blue-600" />
      </div>
      <h1 className="mt-6 text-xl font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.spEvalTitle")}</h1>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t("vizuMultilevel.spEvalSubtitle")}</p>
      <ol className="mt-6 w-full max-w-xs space-y-2 text-left">
        {STEP_KEYS.map((key, i) => (
          <li key={key} className={cn("flex items-center gap-2 text-sm transition-colors", i <= step ? "text-slate-800 dark:text-slate-100" : "text-slate-400")}>
            {i < step ? (
              <CheckCircle2 size={15} className="shrink-0 text-emerald-600" />
            ) : i === step ? (
              <span className="h-2.5 w-2.5 shrink-0 animate-pulse rounded-full bg-orange-500 motion-reduce:animate-none" />
            ) : (
              <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-slate-300 dark:bg-slate-600" />
            )}
            {t(key)}
          </li>
        ))}
      </ol>
      <div className="mt-6 h-2 w-full max-w-sm overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-blue-600 to-orange-500"
          initial={{ width: "4%" }}
          animate={{ width: "92%" }}
          transition={{ duration: 10, ease: "easeOut" }}
        />
      </div>
      <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">{t("vizuMultilevel.spEvalProgress", { done: evaluated, total })}</p>
    </div>
  );
}

function AnimatedNumber({ value }: { value: number }) {
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(reduce ? value : 0);
  useEffect(() => {
    if (reduce) return;
    const controls = animate(0, value, { duration: 1, ease: "easeOut", onUpdate: (v) => setShown(Math.round(v)) });
    return () => controls.stop();
  }, [value, reduce]);
  return <>{reduce ? value : shown}</>;
}

function SprechenResult({ data, onContinue }: { data: VizuMultilevelSpeakingEvaluation; onContinue: () => void }) {
  const { t } = useTranslation();
  const level = data.level === "BELOW_A1" ? t("vizuMultilevel.spBelowA1") : data.level;
  return (
    <div className="mx-auto max-w-4xl space-y-6" data-testid="sprechen-result">
      <motion.section
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="relative overflow-hidden rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-lg)] ring-1 ring-surface-border"
      >
        <span aria-hidden="true" className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-600 via-orange-500 to-blue-600" />
        <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-blue-600">{t("vizuMultilevel.spResultTitle")}</p>
        <p className="mt-4 text-6xl font-extrabold tabular-nums text-[#0f2a4a] dark:text-white">
          <AnimatedNumber value={data.total_score ?? 0} />
          <span className="text-2xl font-bold text-slate-400"> / {data.max_score}</span>
        </p>
        {level && (
          <p className="mt-4 inline-flex items-center gap-2 rounded-full bg-orange-50 px-4 py-1.5 text-sm font-bold text-orange-700 ring-1 ring-orange-200 dark:bg-orange-500/10 dark:text-orange-300">
            {t("vizuMultilevel.determinedLevel")}: {level}
          </p>
        )}
      </motion.section>

      <motion.div
        initial="hidden"
        animate="show"
        variants={{ hidden: {}, show: { transition: { staggerChildren: 0.07, delayChildren: 0.15 } } }}
        className="space-y-3"
      >
        {data.tasks.map((task, i) => (
          <TaskCard key={task.task_id} task={task} defaultOpen={i === 0} />
        ))}
      </motion.div>

      <div className="flex justify-center">
        <Button onClick={onContinue}>
          {t("vizuMultilevel.continueNext")}
          <ArrowRight size={16} />
        </Button>
      </div>
    </div>
  );
}

function TaskCard({ task, defaultOpen }: { task: VizuMultilevelSpeakingTaskEvaluation; defaultOpen: boolean }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(defaultOpen);
  const pct = task.max_score ? Math.round((task.score / task.max_score) * 100) : 0;

  return (
    <motion.div
      variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}
      className="overflow-hidden rounded-2xl bg-surface-card shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
      data-testid="sprechen-task-card"
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50"
      >
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white">
            <Mic size={16} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-bold text-slate-900 dark:text-white">
              {t("vizuMultilevel.aufgabe", { number: task.order_index })} — {task.title}
            </p>
            <div className="mt-1.5 h-1.5 w-40 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-blue-600 to-orange-500"
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.7, delay: 0.2 }}
              />
            </div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span className="text-lg font-extrabold tabular-nums text-slate-900 dark:text-white">
            {task.score}/{task.max_score}
          </span>
          <ChevronDown size={18} className={cn("text-slate-400 transition-transform", open && "rotate-180")} />
        </div>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="space-y-5 border-t border-surface-border px-5 py-5 text-sm">
              <div className="grid gap-2 sm:grid-cols-2">
                {task.criteria.map((c) => (
                  <div key={c.key} className="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-700 dark:text-slate-200">{c.label}</span>
                      <span className="font-bold tabular-nums text-slate-900 dark:text-white">
                        {c.score} / {c.max}
                      </span>
                    </div>
                    <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                      <div className="h-full rounded-full bg-blue-600" style={{ width: `${c.max ? (c.score / c.max) * 100 : 0}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              {task.strengths.length > 0 && (
                <Section icon={<CheckCircle2 size={14} className="text-emerald-600" />} title={t("vizuMultilevel.spStrengths")}>
                  <ul className="list-disc space-y-1 pl-5 text-slate-700 dark:text-slate-200">
                    {task.strengths.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </Section>
              )}

              {task.improvements.length > 0 && (
                <Section icon={<TrendingUp size={14} className="text-orange-500" />} title={t("vizuMultilevel.spImprovements")}>
                  <ul className="list-disc space-y-1 pl-5 text-slate-700 dark:text-slate-200">
                    {task.improvements.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </Section>
              )}

              <Section title={t("vizuMultilevel.spErrors")}>
                {task.errors.length === 0 ? (
                  <p className="text-slate-600 dark:text-slate-300">{t("vizuMultilevel.spNoErrors")}</p>
                ) : (
                  <div className="space-y-2">
                    {task.errors.map((e, i) => (
                      <div key={i} className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-slate-700">
                        <p>
                          <span className="font-semibold text-slate-500">{t("vizuMultilevel.spSaid")}:</span>{" "}
                          <span className="text-red-600 dark:text-red-400">„{e.original}“</span>
                        </p>
                        <p>
                          <span className="font-semibold text-slate-500">{t("vizuMultilevel.spBetter")}:</span>{" "}
                          <span className="font-semibold text-emerald-700 dark:text-emerald-400">„{e.correction}“</span>
                        </p>
                        <p className="text-slate-600 dark:text-slate-300">
                          <span className="font-semibold text-slate-500">{t("vizuMultilevel.spWhy")}:</span> {e.explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </Section>

              {task.feedback && (
                <Section title={t("vizuMultilevel.spFeedback")}>
                  <p className="leading-relaxed text-slate-700 dark:text-slate-200">{task.feedback}</p>
                </Section>
              )}

              {task.next_step && (
                <div className="flex gap-2 rounded-xl bg-orange-50 p-3 text-orange-900 ring-1 ring-orange-200 dark:bg-orange-500/10 dark:text-orange-200 dark:ring-orange-500/30">
                  <Lightbulb size={16} className="mt-0.5 shrink-0" />
                  <p>
                    <span className="font-bold">{t("vizuMultilevel.spTip")}: </span>
                    {task.next_step}
                  </p>
                </div>
              )}

              {task.teacher_comment && (
                <Section title={t("vizuMultilevel.spTeacherComment")}>
                  <p className="text-slate-700 dark:text-slate-200">{task.teacher_comment}</p>
                </Section>
              )}

              {task.transcript && (
                <details className="rounded-xl bg-slate-50 p-3 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  <summary className="cursor-pointer text-xs font-bold uppercase tracking-wide text-slate-500">
                    {t("vizuMultilevel.spTranscript")}
                  </summary>
                  <p className="mt-2 leading-relaxed">{task.transcript}</p>
                </details>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function Section({ title, icon, children }: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-blue-700 dark:text-blue-300">
        {icon}
        {title}
      </p>
      {children}
    </div>
  );
}
