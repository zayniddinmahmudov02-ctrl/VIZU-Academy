"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { animate, motion, useReducedMotion } from "framer-motion";
import { AlertCircle, ArrowRight, Award, CheckCircle2, Compass, RefreshCw, TrendingUp } from "lucide-react";

import Button from "@/components/ui/button";
import VizuMultilevelCertificateDownload from "@/features/vizu-multilevel/components/certificate-download";
import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MULTILEVEL_SKILLS, stepPath } from "@/features/vizu-multilevel/constants/skills";
import {
  completeVizuMultilevelAttempt,
  getMyVizuMultilevelResults,
  getVizuMultilevelAttemptState,
  getVizuMultilevelResult,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";
import type {
  VizuMultilevelAttemptResult,
  VizuMultilevelCompetencyResult,
  VizuMultilevelSkill,
} from "@/features/vizu-multilevel/types/vizu-multilevel.types";

type Band = "strong" | "mid" | "weak";

function band(percentage: number): Band {
  if (percentage >= 75) return "strong";
  if (percentage >= 50) return "mid";
  return "weak";
}

/** Results (Ergebnis). Finishing happens here: the server only completes the
 * attempt once all four competencies are submitted — otherwise this page
 * lists exactly which ones are still open. A finished attempt is never
 * completed twice; its result is just read back. */
export default function VizuMultilevelResultsPage() {
  const { t } = useTranslation();
  const { attemptId } = useParams<{ attemptId: string }>();
  const queryClient = useQueryClient();
  const completedOnce = useRef(false);

  const state = useQuery({
    queryKey: ["vizu-multilevel-state", attemptId],
    queryFn: () => getVizuMultilevelAttemptState(attemptId),
    retry: false,
  });

  const missing = (state.data?.sections ?? []).filter((s) => !s.submitted).map((s) => s.skill);
  const isFinished = state.data?.status === "COMPLETED";
  const readyToComplete = state.data?.status === "IN_PROGRESS" && missing.length === 0;

  const complete = useMutation({
    mutationFn: () => completeVizuMultilevelAttempt(attemptId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-current"] });
      queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-my-results"] });
      queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-state", attemptId] });
    },
  });

  useEffect(() => {
    if (readyToComplete && !completedOnce.current) {
      completedOnce.current = true;
      complete.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readyToComplete]);

  const result = useQuery({
    queryKey: ["vizu-multilevel-result", attemptId],
    queryFn: () => getVizuMultilevelResult(attemptId),
    enabled: isFinished,
  });

  const data: VizuMultilevelAttemptResult | undefined = complete.data?.result ?? result.data;

  if (state.isLoading || complete.isPending || (isFinished && result.isLoading)) {
    return <p className="py-16 text-center text-sm text-text-secondary">{t("common.loading")}</p>;
  }

  if (state.isError || complete.isError || result.isError) {
    return (
      <div className="mx-auto max-w-md rounded-card bg-surface-card p-8 text-center ring-1 ring-surface-border">
        <AlertCircle size={30} className="mx-auto text-orange-500" />
        <p className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">{t("vizuMultilevel.loadError")}</p>
        <Button variant="secondary" className="mt-4" onClick={() => window.location.reload()}>
          <RefreshCw size={15} />
          {t("vizuMultilevel.retry")}
        </Button>
      </div>
    );
  }

  if (!isFinished && missing.length > 0) {
    return <MissingCompetencies attemptId={attemptId} missing={missing} />;
  }

  if (!data) return null;
  return <ResultScreen data={data} />;
}

/** The certificate level once the result is final: A1..C1, or "BELOW_A1"
 * when every competency is graded and the overall result is below A1. */
function certificateLevel(data: VizuMultilevelAttemptResult): string | null {
  const allGraded = data.competencies.every((c) => c.status === "GRADED" || c.status === "NO_CONTENT");
  if (!allGraded) return null;
  if (data.overall.status === "FINAL") return data.overall.level;
  return data.overall.status === "BELOW_A1" ? "BELOW_A1" : null;
}

function MissingCompetencies({ attemptId, missing }: { attemptId: string; missing: VizuMultilevelSkill[] }) {
  const { t } = useTranslation();
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mx-auto max-w-lg space-y-5">
      <div className="rounded-card bg-surface-card p-8 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h1 className="text-lg font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.missingTitle")}</h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t("vizuMultilevel.missingBody")}</p>
        <ul className="mt-5 space-y-2">
          {missing.map((skill) => {
            const meta = VIZU_MULTILEVEL_SKILLS.find((s) => s.skill === skill)!;
            const Icon = meta.icon;
            return (
              <li key={skill}>
                <Link
                  href={stepPath(attemptId, skill)}
                  className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900 ring-1 ring-slate-200 transition-colors hover:bg-blue-50 hover:ring-blue-300 dark:bg-slate-800 dark:text-white dark:ring-slate-700"
                >
                  <span className="flex items-center gap-2">
                    <Icon size={16} className="text-blue-600" />
                    {t(meta.labelKey)}
                  </span>
                  <ArrowRight size={15} className="text-orange-500" />
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </motion.div>
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

function ResultScreen({ data }: { data: VizuMultilevelAttemptResult }) {
  const { t } = useTranslation();
  const mine = useQuery({ queryKey: ["vizu-multilevel-my-results"], queryFn: getMyVizuMultilevelResults });
  const maxAttempts = data.max_attempts ?? mine.data?.max_attempts ?? 3;
  const graded = data.competencies.filter((c) => c.status === "GRADED" && c.max_score && c.percentage !== null);
  const pending = data.competencies.filter((c) => c.status === "PENDING_REVIEW");
  const overallPercent = graded.length
    ? Math.round(graded.reduce((sum, c) => sum + (c.percentage ?? 0), 0) / graded.length)
    : null;
  const rawTotal = graded.reduce((sum, c) => sum + (c.raw_score ?? 0), 0);
  const maxTotal = graded.reduce((sum, c) => sum + (c.max_score ?? 0), 0);

  const strengths = graded.filter((c) => band(c.percentage!) === "strong");
  const improvements = [...graded].filter((c) => band(c.percentage!) !== "strong").sort((a, b) => a.percentage! - b.percentage!);
  const weakest = [...graded].sort((a, b) => a.percentage! - b.percentage!)[0];
  const overall = data.overall;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Central score card */}
      <motion.section
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10"
      >
        <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-blue-600">{t("vizuMultilevel.title")}</p>
        {data.attempt_number ? (
          <p className="mt-2 inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-200" data-testid="attempt-of">
            {t("vizuMultilevel.attemptOf", { n: data.attempt_number, max: maxAttempts })}
          </p>
        ) : null}
        <p className="mt-1 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{t("vizuMultilevel.resultHeading")}</p>
        <p className="mt-5 text-6xl font-extrabold tabular-nums text-slate-900 dark:text-white">
          {overallPercent === null ? "—" : <AnimatedNumber value={overallPercent} />}
          <span className="text-2xl font-bold text-slate-400"> / 100</span>
        </p>
        {overallPercent !== null && (
          <>
            <p className="mt-1 text-lg font-bold text-orange-500">
              <AnimatedNumber value={overallPercent} />%
            </p>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              {t("vizuMultilevel.totalPoints")}: {rawTotal} / {maxTotal}
            </p>
          </>
        )}
        <div className="mx-auto mt-5 inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-1.5 text-sm font-bold text-blue-700 dark:bg-blue-500/15 dark:text-blue-300">
          <Award size={15} />
          {t("vizuMultilevel.resultsOverall")}:{" "}
          {overall.status === "FINAL"
            ? overall.level
            : overall.status === "BELOW_A1"
              ? t("vizuMultilevel.belowA1")
              : overall.status === "PENDING_REVIEW"
                ? t("vizuMultilevel.pendingReview")
                : "—"}
        </div>
        {pending.length > 0 && <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">{t("vizuMultilevel.pendingReviewNote")}</p>}
        {mine.data && (
          <p className="mt-3 text-xs font-medium text-slate-500 dark:text-slate-400" data-testid="attempts-used">
            {t("vizuMultilevel.attemptsUsed", { used: mine.data.attempts_used, max: mine.data.max_attempts })}
          </p>
        )}
      </motion.section>

      {/* Competency cards */}
      <motion.div
        initial="hidden"
        animate="show"
        variants={{ hidden: {}, show: { transition: { staggerChildren: 0.07, delayChildren: 0.15 } } }}
        className="grid gap-4 sm:grid-cols-2"
      >
        {VIZU_MULTILEVEL_SKILLS.map((s) => (
          <CompetencyCard key={s.skill} meta={s} competency={data.competencies.find((c) => c.skill === s.skill)} />
        ))}
      </motion.div>

      {/* Certificate for every final result: A1-C1 or "unter A1" (null = review still running) */}
      {(overall.status === "FINAL" || overall.status === "BELOW_A1") && (
        <VizuMultilevelCertificateDownload attemptId={data.attempt_id} level={certificateLevel(data)} />
      )}

      {/* Feedback */}
      {graded.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45, duration: 0.3 }}
          className="grid gap-4 md:grid-cols-3"
        >
          <FeedbackBox icon={<CheckCircle2 size={16} className="text-emerald-600" />} title={t("vizuMultilevel.strengths")}>
            {strengths.length === 0 ? (
              <p>{t("vizuMultilevel.noStrengthsYet")}</p>
            ) : (
              strengths.map((c) => <p key={c.skill}>{t(`vizuMultilevel.fb_${c.skill}_strong`)}</p>)
            )}
          </FeedbackBox>
          <FeedbackBox icon={<TrendingUp size={16} className="text-orange-500" />} title={t("vizuMultilevel.improvements")}>
            {improvements.length === 0 ? (
              <p>{t("vizuMultilevel.noImprovementsNeeded")}</p>
            ) : (
              improvements.map((c) => <p key={c.skill}>{t(`vizuMultilevel.fb_${c.skill}_${band(c.percentage!)}`)}</p>)
            )}
          </FeedbackBox>
          <FeedbackBox icon={<Compass size={16} className="text-blue-600" />} title={t("vizuMultilevel.nextSteps")}>
            {weakest && <p>{t(`vizuMultilevel.next_${weakest.skill}_${band(weakest.percentage!)}`)}</p>}
          </FeedbackBox>
        </motion.section>
      )}

      <div className="flex justify-center">
        <Link href="/vizu-multilevel">
          <Button variant="ghost">{t("vizuMultilevel.backToHub")}</Button>
        </Link>
      </div>
    </div>
  );
}

function CompetencyCard({
  meta,
  competency,
}: {
  meta: (typeof VIZU_MULTILEVEL_SKILLS)[number];
  competency: VizuMultilevelCompetencyResult | undefined;
}) {
  const { t } = useTranslation();
  const Icon = meta.icon;
  const pct = competency?.percentage ?? null;

  let value: string;
  if (!competency || competency.status === "NO_CONTENT") value = t("vizuMultilevel.notAvailable");
  else if (competency.status === "PENDING_REVIEW") value = t("vizuMultilevel.pendingReview");
  else if (competency.status === "NOT_SUBMITTED") value = t("vizuMultilevel.resultsPending");
  else value = `${competency.raw_score ?? 0} / ${competency.max_score ?? 0}`;

  return (
    <motion.div
      variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } }}
      whileHover={{ y: -3 }}
      className="rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
            <Icon size={18} />
          </div>
          <p className="text-sm font-extrabold uppercase tracking-wide text-slate-900 dark:text-white">{t(meta.labelKey)}</p>
        </div>
        {competency?.status === "GRADED" && (
          <span className="rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-bold text-orange-700 dark:bg-orange-500/15 dark:text-orange-300">
            {competency.level ?? t("vizuMultilevel.belowA1")}
          </span>
        )}
      </div>
      <p className="mt-4 text-2xl font-bold tabular-nums text-slate-900 dark:text-white">{value}</p>
      {pct !== null && competency?.status === "GRADED" && (
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-orange-500 to-orange-400"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          />
        </div>
      )}
    </motion.div>
  );
}

function FeedbackBox({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
      <p className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
        {icon}
        {title}
      </p>
      <div className="mt-3 space-y-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{children}</div>
    </div>
  );
}
