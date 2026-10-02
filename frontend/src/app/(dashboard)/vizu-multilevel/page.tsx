"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertCircle, Award, Clock3, Gauge, Hourglass, Lock, PlayCircle, RefreshCw } from "lucide-react";

import Button from "@/components/ui/button";
import PageHeader from "@/components/dashboard/page-header";
import { cardEntrance, fadeInUp, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MULTILEVEL_SKILLS, stepPath } from "@/features/vizu-multilevel/constants/skills";
import {
  createVizuMultilevelAttempt,
  getCurrentVizuMultilevelAttempt,
  getVizuMultilevelAttemptState,
  getVizuMultilevelAvailability,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";

/** Start page. A student has exactly ONE attempt (enforced by the server):
 * no attempt yet -> "Start"; attempt running -> "Continue" (the same
 * attempt, at the competency the server says is next); attempt finished ->
 * "View result". There is no attempt history. */
export default function VizuMultilevelHubPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const queryClient = useQueryClient();

  const availability = useQuery({ queryKey: ["vizu-multilevel-availability"], queryFn: getVizuMultilevelAvailability });
  const current = useQuery({ queryKey: ["vizu-multilevel-current"], queryFn: getCurrentVizuMultilevelAttempt });

  const startMutation = useMutation({
    mutationFn: createVizuMultilevelAttempt,
    onSuccess: (attempt) => {
      queryClient.setQueryData(["vizu-multilevel-current"], attempt);
      router.push(stepPath(attempt.id, "lesen"));
    },
    // 409 = the student already has their one attempt — show it instead.
    onError: () => queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-current"] }),
  });

  const continueMutation = useMutation({
    mutationFn: (attemptId: string) => getVizuMultilevelAttemptState(attemptId),
    onSuccess: (state) => router.push(stepPath(state.attempt_id, state.next_skill ?? "natijalar")),
  });

  const loading = availability.isLoading || current.isLoading;
  const failed = availability.isError || current.isError;
  const attempt = current.data ?? null;
  const notAvailable = availability.data && !availability.data.available && !attempt;

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
              void current.refetch();
            }}
          >
            <RefreshCw size={15} />
            {t("vizuMultilevel.retry")}
          </Button>
        </div>
      )}

      {!loading && !failed && (
        <motion.section
          variants={fadeInUp}
          initial="hidden"
          animate="show"
          className="relative overflow-hidden rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-8"
        >
          <span className="inline-block rounded-full bg-orange-100 px-3 py-1 text-xs font-bold tracking-wide text-orange-700 dark:bg-orange-500/15 dark:text-orange-300">
            {t("vizuMultilevel.levelRange")}
          </span>
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
            ) : !attempt ? (
              <motion.div whileTap={{ scale: 0.97 }} className="inline-block">
                <Button onClick={() => startMutation.mutate()} disabled={startMutation.isPending} size="lg">
                  <PlayCircle size={18} />
                  {startMutation.isPending ? t("common.loading") : t("vizuMultilevel.startTest")}
                </Button>
              </motion.div>
            ) : attempt.status === "IN_PROGRESS" ? (
              <motion.div whileTap={{ scale: 0.97 }} className="inline-block">
                <Button onClick={() => continueMutation.mutate(attempt.id)} disabled={continueMutation.isPending} size="lg">
                  <PlayCircle size={18} />
                  {continueMutation.isPending ? t("common.loading") : t("vizuMultilevel.continueTest")}
                </Button>
              </motion.div>
            ) : (
              <motion.div whileTap={{ scale: 0.97 }} className="inline-block">
                <Button onClick={() => router.push(stepPath(attempt.id, "natijalar"))} size="lg">
                  <Award size={18} />
                  {t("vizuMultilevel.viewResult")}
                </Button>
              </motion.div>
            )}
          </div>
        </motion.section>
      )}

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
