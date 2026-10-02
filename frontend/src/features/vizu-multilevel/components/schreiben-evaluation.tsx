"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, animate, motion, useReducedMotion } from "framer-motion";
import { AlertCircle, ArrowRight, CheckCircle2, ChevronDown, Compass, PenLine, RefreshCw, TrendingUp } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import {
  getVizuMultilevelSchreibenEvaluation,
  retryVizuMultilevelSchreibenEvaluation,
} from "../services/vizu-multilevel-service";
import type { VizuMultilevelWritingEvaluation, VizuMultilevelWritingTaskEvaluation } from "../types/vizu-multilevel.types";

const STEP_KEYS = [
  "vizuMultilevel.evalStepTask",
  "vizuMultilevel.evalStepGrammar",
  "vizuMultilevel.evalStepVocabulary",
  "vizuMultilevel.evalStepStructure",
  "vizuMultilevel.evalStepFeedback",
];

/** After the final submission: an evaluation screen for at least
 * `minDurationMs` (10 s after a fresh submission) that stays until the
 * server reports the REAL evaluation as DONE — a result is never faked.
 * FAILED (e.g. AI temporarily unavailable) shows a retry instead. */
export default function SchreibenEvaluationFlow({
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
    queryKey: ["vizu-multilevel-schreiben-evaluation", attemptId],
    queryFn: () => getVizuMultilevelSchreibenEvaluation(attemptId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "DONE" || status === "FAILED" ? false : 2500;
    },
  });

  const retry = useMutation({
    mutationFn: () => retryVizuMultilevelSchreibenEvaluation(attemptId),
    onSettled: () => void evaluation.refetch(),
  });

  const data = evaluation.data;
  if (data?.status === "DONE" && minElapsed) {
    return <SchreibenResult data={data} onContinue={onContinue} />;
  }
  if ((data?.status === "FAILED" || evaluation.isError) && minElapsed && !retry.isPending) {
    return (
      <div className="mx-auto max-w-md rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <AlertCircle size={30} className="mx-auto text-orange-500" />
        <p className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">{t("vizuMultilevel.evalFailed")}</p>
        <Button className="mt-4" onClick={() => retry.mutate()}>
          <RefreshCw size={15} />
          {t("vizuMultilevel.evalRetry")}
        </Button>
      </div>
    );
  }
  return <EvaluatingScreen evaluated={data?.evaluated ?? 0} total={data?.total_tasks ?? 5} />;
}

function EvaluatingScreen({ evaluated, total }: { evaluated: number; total: number }) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const [step, setStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setStep((s) => (s + 1) % STEP_KEYS.length), 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mx-auto flex min-h-[420px] max-w-xl flex-col items-center justify-center rounded-card bg-surface-card p-10 text-center shadow-[var(--shadow-lg)] ring-1 ring-surface-border">
      <motion.div
        animate={reduce ? undefined : { rotate: 360 }}
        transition={{ repeat: Infinity, duration: 2.4, ease: "linear" }}
        className="flex h-16 w-16 items-center justify-center rounded-full border-4 border-blue-100 border-t-orange-500"
        aria-hidden="true"
      />
      <h1 className="mt-6 text-xl font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.evalTitle")}</h1>
      <div className="mt-3 h-6">
        <AnimatePresence mode="wait">
          <motion.p
            key={step}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.25 }}
            className="text-sm text-slate-600 dark:text-slate-300"
          >
            {t(STEP_KEYS[step])}
          </motion.p>
        </AnimatePresence>
      </div>
      <div className="mt-6 h-2 w-full max-w-sm overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-blue-600 to-orange-500"
          initial={{ width: "4%" }}
          animate={{ width: "92%" }}
          transition={{ duration: 10, ease: "easeOut" }}
        />
      </div>
      <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
        {t("vizuMultilevel.evalProgress", { done: evaluated, total })}
      </p>
    </div>
  );
}

function AnimatedNumber({ value }: { value: number }) {
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(reduce ? value : 0);
  useEffect(() => {
    if (reduce) return;
    const controls = animate(0, value, { duration: 0.9, ease: "easeOut", onUpdate: (v) => setShown(Math.round(v)) });
    return () => controls.stop();
  }, [value, reduce]);
  return <>{reduce ? value : shown}</>;
}

function SchreibenResult({ data, onContinue }: { data: VizuMultilevelWritingEvaluation; onContinue: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <motion.section
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-lg)] ring-1 ring-surface-border"
      >
        <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-blue-600">{t("vizuMultilevel.writingResultTitle")}</p>
        <p className="mt-4 text-5xl font-extrabold tabular-nums text-slate-900 dark:text-white">
          <AnimatedNumber value={data.total_score ?? 0} />
          <span className="text-2xl font-bold text-slate-400"> / {data.max_score}</span>
        </p>
        <p className="mt-1 text-sm font-semibold text-orange-500">{t("vizuMultilevel.pointsUnit")}</p>
      </motion.section>

      <motion.div
        initial="hidden"
        animate="show"
        variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06, delayChildren: 0.1 } } }}
        className="space-y-3"
      >
        {data.tasks.map((task, i) => (
          <TaskCard key={task.task_id} task={task} defaultOpen={i === 0} />
        ))}
      </motion.div>

      {data.summary && (
        <section className="grid gap-4 md:grid-cols-3">
          <SummaryBox icon={<CheckCircle2 size={16} className="text-emerald-600" />} title={t("vizuMultilevel.overallGood")} items={data.summary.good} />
          <SummaryBox icon={<TrendingUp size={16} className="text-orange-500" />} title={t("vizuMultilevel.overallImprove")} items={data.summary.improve} />
          <SummaryBox icon={<Compass size={16} className="text-blue-600" />} title={t("vizuMultilevel.overallNext")} items={data.summary.next} />
        </section>
      )}

      <div className="flex justify-center">
        <Button onClick={onContinue}>
          {t("vizuMultilevel.continueNext")}
          <ArrowRight size={16} />
        </Button>
      </div>
    </div>
  );
}

function TaskCard({ task, defaultOpen }: { task: VizuMultilevelWritingTaskEvaluation; defaultOpen: boolean }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(defaultOpen);
  const pct = task.max_score ? Math.round((task.score / task.max_score) * 100) : 0;

  return (
    <motion.div
      variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}
      className="overflow-hidden rounded-2xl bg-surface-card shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50"
      >
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white">
            <PenLine size={16} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-bold text-slate-900 dark:text-white">
              {t("vizuMultilevel.aufgabe", { number: task.order_index })} — {task.title}
            </p>
            <div className="mt-1.5 h-1.5 w-40 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-orange-500 to-orange-400"
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.7, delay: 0.2 }}
              />
            </div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span className="text-lg font-extrabold tabular-nums text-slate-900 dark:text-white">
            {task.score} / {task.max_score}
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
                  <div key={c.name} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800">
                    <span className="text-slate-700 dark:text-slate-200">{c.name}</span>
                    <span className="font-bold tabular-nums text-slate-900 dark:text-white">
                      {c.score} / {c.max}
                    </span>
                  </div>
                ))}
              </div>

              <Section title={t("vizuMultilevel.strengthsTitle")}>
                <ul className="list-disc space-y-1 pl-5 text-slate-700 dark:text-slate-200">
                  {task.strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </Section>

              <Section title={t("vizuMultilevel.errorsTitle")}>
                {task.errors.length === 0 ? (
                  <p className="text-slate-600 dark:text-slate-300">{t("vizuMultilevel.noErrors")}</p>
                ) : (
                  <div className="space-y-2">
                    {task.errors.map((e, i) => (
                      <div key={i} className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-slate-700">
                        <p>
                          <span className="font-semibold text-slate-500">{t("vizuMultilevel.originalLabel")}:</span>{" "}
                          <span className="text-red-600 line-through decoration-red-400 dark:text-red-400">{e.original}</span>
                        </p>
                        <p>
                          <span className="font-semibold text-slate-500">{t("vizuMultilevel.correctionLabel")}:</span>{" "}
                          <span className="font-semibold text-emerald-700 dark:text-emerald-400">{e.correction}</span>
                        </p>
                        <p className="text-slate-600 dark:text-slate-300">
                          <span className="font-semibold text-slate-500">{t("vizuMultilevel.whyLabel")}:</span> {e.explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </Section>

              <Section title={t("vizuMultilevel.feedbackTitle")}>
                <p className="leading-relaxed text-slate-700 dark:text-slate-200">{task.feedback}</p>
              </Section>

              <Section title={t("vizuMultilevel.nextStepTitle")}>
                <ul className="list-disc space-y-1 pl-5 text-slate-700 dark:text-slate-200">
                  {task.next_steps.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </Section>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1.5 text-xs font-bold uppercase tracking-wide text-blue-700 dark:text-blue-300">{title}</p>
      {children}
    </div>
  );
}

function SummaryBox({ icon, title, items }: { icon: React.ReactNode; title: string; items: string[] }) {
  return (
    <div className="rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
      <p className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
        {icon}
        {title}
      </p>
      <ul className="mt-3 space-y-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
