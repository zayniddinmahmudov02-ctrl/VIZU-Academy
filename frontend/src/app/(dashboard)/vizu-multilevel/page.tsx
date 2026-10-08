"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertCircle, ArrowRight, Award, Clock3, Gauge, Hourglass, Lock, PlayCircle, RefreshCw, Trophy } from "lucide-react";

import Button from "@/components/ui/button";
import PageHeader from "@/components/dashboard/page-header";
import { cardEntrance, fadeInUp, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MULTILEVEL_SKILLS, stepPath } from "@/features/vizu-multilevel/constants/skills";
import {
  createVizuMultilevelAttempt,
  getMyVizuMultilevelResults,
  getVizuMultilevelAttemptState,
  getVizuMultilevelAvailability,
  isMaxAttemptsError,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";
import type { VizuMultilevelAttemptSummary } from "@/features/vizu-multilevel/types/vizu-multilevel.types";

/** Start page. A student has up to 3 attempts (enforced by the server):
 * a running attempt -> "Continue"; otherwise, while attempts are left ->
 * "Start" / "Neuen Versuch starten"; afterwards "Keine weiteren Versuche
 * verfügbar." Below: "Bestes Ergebnis" and "Meine Ergebnisse" (own attempts
 * only — the server never returns another student's data). */
export default function VizuMultilevelHubPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const queryClient = useQueryClient();

  const availability = useQuery({ queryKey: ["vizu-multilevel-availability"], queryFn: getVizuMultilevelAvailability });
  const mine = useQuery({ queryKey: ["vizu-multilevel-my-results"], queryFn: getMyVizuMultilevelResults });

  const startMutation = useMutation({
    mutationFn: createVizuMultilevelAttempt,
    onSuccess: (attempt) => {
      queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-my-results"] });
      queryClient.setQueryData(["vizu-multilevel-current"], attempt);
      router.push(stepPath(attempt.id, "lesen"));
    },
    // 409 (attempt running) / 403 (all attempts used): show the real state.
    onError: () => queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-my-results"] }),
  });

  const continueMutation = useMutation({
    mutationFn: (attemptId: string) => getVizuMultilevelAttemptState(attemptId),
    onSuccess: (state) => router.push(stepPath(state.attempt_id, state.next_skill ?? "natijalar")),
  });

  const loading = availability.isLoading || mine.isLoading;
  const failed = availability.isError || mine.isError;
  const data = mine.data;
  const notAvailable = availability.data && !availability.data.available && !data?.attempts_used;
  const maxAttempts = data?.max_attempts ?? 3;
  const limitReached = !!data && !data.in_progress_attempt_id && data.attempts_remaining === 0;
  const running = data?.attempts.find((a) => a.id === data.in_progress_attempt_id) ?? null;

  return (
    <div className="space-y-10">
      <PageHeader icon={Gauge} titleKey="vizuMultilevel.title" subtitleKey="vizuMultilevel.subtitle" gradient="from-blue-600 to-blue-500" />

      {loading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {failed && !loading && (
        <div className="rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
          <AlertCircle size={30} className="mx-auto text-orange-500" />
          <p className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">{t("vizuMultilevel.loadError")}</p>
          <Button
            variant="secondary"
            className="mt-4"
            onClick={() => {
              void availability.refetch();
              void mine.refetch();
            }}
          >
            <RefreshCw size={15} />
            {t("vizuMultilevel.retry")}
          </Button>
        </div>
      )}

      {!loading && !failed && data && (
        <motion.section
          variants={fadeInUp}
          initial="hidden"
          animate="show"
          className="relative overflow-hidden rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-8"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-block rounded-full bg-orange-100 px-3 py-1 text-xs font-bold tracking-wide text-orange-700 dark:bg-orange-500/15 dark:text-orange-300">
              {t("vizuMultilevel.levelRange")}
            </span>
            {data.attempts_used > 0 && (
              <span className="inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-200" data-testid="attempts-used">
                {t("vizuMultilevel.attemptsUsed", { used: data.attempts_used, max: maxAttempts })}
              </span>
            )}
          </div>
          <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl dark:text-white">{t("vizuMultilevel.heroTitle")}</h2>
          <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">{t("vizuMultilevel.heroBody")}</p>
          <p className="mt-3 flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            <Lock size={15} className="text-blue-600" />
            {t("vizuMultilevel.oneAttemptNote")}
          </p>

          <div className="mt-6">
            {notAvailable ? (
              <div className="flex items-center gap-3 rounded-xl bg-slate-50 p-4 text-sm text-slate-700 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700">
                <Hourglass size={18} className="text-orange-500" />
                {t("vizuMultilevel.notAvailableYet")}
              </div>
            ) : running ? (
              <div className="flex flex-wrap items-center gap-3">
                <motion.div whileTap={{ scale: 0.97 }} className="inline-block">
                  <Button onClick={() => continueMutation.mutate(running.id)} disabled={continueMutation.isPending} size="lg">
                    <PlayCircle size={18} />
                    {continueMutation.isPending ? t("common.loading") : t("vizuMultilevel.continueTest")}
                  </Button>
                </motion.div>
                <span className="text-sm font-semibold text-slate-600 dark:text-slate-300" data-testid="attempt-of">
                  {t("vizuMultilevel.attemptOf", { n: running.attempt_number ?? data.attempts_used, max: maxAttempts })}
                </span>
              </div>
            ) : limitReached || isMaxAttemptsError(startMutation.error) ? (
              <div className="rounded-xl bg-slate-50 p-4 ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-slate-700" data-testid="no-more-attempts">
                <p className="text-sm font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.noMoreAttempts")}</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t("vizuMultilevel.allAttemptsUsed", { max: maxAttempts })}</p>
              </div>
            ) : (
              <div className="flex flex-wrap items-center gap-3">
                <motion.div whileTap={{ scale: 0.97 }} className="inline-block">
                  <Button onClick={() => startMutation.mutate()} disabled={startMutation.isPending} size="lg" data-testid="start-attempt">
                    <PlayCircle size={18} />
                    {startMutation.isPending
                      ? t("common.loading")
                      : data.attempts_used === 0
                        ? t("vizuMultilevel.startTest")
                        : t("vizuMultilevel.newAttempt")}
                  </Button>
                </motion.div>
                <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                  {t("vizuMultilevel.attemptOf", { n: data.attempts_used + 1, max: maxAttempts })}
                </span>
              </div>
            )}
          </div>
        </motion.section>
      )}

      {!loading && !failed && data?.best && <BestResultCard best={data.best} maxAttempts={maxAttempts} />}

      {!loading && !failed && data && data.attempts.length > 0 && <MyResults attempts={data.attempts} maxAttempts={maxAttempts} />}

      <section>
        <h2 className="mb-5 text-base font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.howItWorks")}</h2>
        <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {VIZU_MULTILEVEL_SKILLS.map((s) => {
            const Icon = s.icon;
            return (
              <motion.div
                key={s.skill}
                variants={cardEntrance}
                whileHover={{ y: -3 }}
                className="rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow">
                  <Icon size={18} />
                </div>
                <p className="mt-3 font-semibold text-slate-900 dark:text-white">{t(s.labelKey)}</p>
                <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                  <Clock3 size={12} /> {t("vizuMultilevel.minutesEach")}
                </p>
              </motion.div>
            );
          })}
        </motion.div>
        <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">{t("vizuMultilevel.totalDuration")}</p>
      </section>
    </div>
  );
}

function useLevelText() {
  const { t } = useTranslation();
  return (level: string | null) => (level === "BELOW_A1" ? t("vizuMultilevel.belowA1") : level ?? "—");
}

function BestResultCard({ best, maxAttempts }: { best: VizuMultilevelAttemptSummary; maxAttempts: number }) {
  const { t } = useTranslation();
  const levelText = useLevelText();
  return (
    <motion.section
      variants={fadeInUp}
      initial="hidden"
      animate="show"
      className="flex items-center gap-5 rounded-card bg-gradient-to-br from-blue-600 to-blue-500 p-6 text-white shadow-[var(--shadow-md)] sm:p-7"
      data-testid="best-result"
    >
      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-white/15">
        <Trophy size={26} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-white/80">{t("vizuMultilevel.bestResult")}</p>
        <p className="mt-1 text-3xl font-extrabold tabular-nums">
          {best.result_score} <span className="text-lg font-bold text-white/70">/ 100</span>
        </p>
        <p className="mt-0.5 text-sm font-semibold text-white/90">
          {t("vizuMultilevel.levelName", { level: levelText(best.result_level) })}
          {best.attempt_number ? ` · ${t("vizuMultilevel.attemptOf", { n: best.attempt_number, max: maxAttempts })}` : ""}
        </p>
      </div>
    </motion.section>
  );
}

function MyResults({ attempts, maxAttempts }: { attempts: VizuMultilevelAttemptSummary[]; maxAttempts: number }) {
  const { t } = useTranslation();
  const levelText = useLevelText();
  return (
    <section>
      <h2 className="mb-4 text-base font-bold text-slate-900 dark:text-white">{t("vizuMultilevel.myResults")}</h2>
      <ul className="space-y-2" data-testid="my-results">
        {attempts.map((a) => {
          const running = a.status === "IN_PROGRESS";
          const detail = running
            ? t("vizuMultilevel.attemptRunning")
            : a.result_score === null
              ? t("vizuMultilevel.attemptPending")
              : `${a.result_score} / 100 — ${levelText(a.result_level)}`;
          return (
            <li key={a.id}>
              <Link
                href={stepPath(a.id, "natijalar")}
                className="flex items-center justify-between gap-3 rounded-xl bg-surface-card px-4 py-3 text-sm shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-colors hover:ring-blue-300"
              >
                <span className="flex min-w-0 items-center gap-2 font-semibold text-slate-900 dark:text-white">
                  <Award size={16} className="shrink-0 text-blue-600" />
                  {t("vizuMultilevel.attemptOf", { n: a.attempt_number ?? "?", max: maxAttempts })}
                </span>
                <span className="flex items-center gap-2 font-bold tabular-nums text-slate-700 dark:text-slate-200">
                  {detail}
                  <ArrowRight size={15} className="text-orange-500" />
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
