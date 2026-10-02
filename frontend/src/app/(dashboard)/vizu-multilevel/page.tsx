"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Award, Clock3, Gauge, PlayCircle } from "lucide-react";

import Button from "@/components/ui/button";
import PageHeader from "@/components/dashboard/page-header";
import { cardEntrance, fadeInUp, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MULTILEVEL_SKILLS } from "@/features/vizu-multilevel/constants/skills";
import { createVizuMultilevelAttempt, listVizuMultilevelAttempts } from "@/features/vizu-multilevel/services/vizu-multilevel-service";

export default function VizuMultilevelHubPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: attempts, isLoading } = useQuery({
    queryKey: ["vizu-multilevel-attempts"],
    queryFn: listVizuMultilevelAttempts,
  });

  const startMutation = useMutation({
    mutationFn: createVizuMultilevelAttempt,
    onSuccess: (attempt) => router.push(`/vizu-multilevel/${attempt.id}/lesen`),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-attempts"] }),
  });

  return (
    <div className="space-y-10">
      <PageHeader icon={Gauge} titleKey="vizuMultilevel.title" subtitleKey="vizuMultilevel.subtitle" gradient="from-accent-blue to-accent-purple" />

      {/* Hero */}
      <motion.section
        variants={fadeInUp}
        initial="hidden"
        animate="show"
        className="relative overflow-hidden rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-6 text-white shadow-[var(--shadow-lg)] sm:p-8"
      >
        <span className="inline-block rounded-full bg-white/15 px-3 py-1 text-xs font-bold tracking-wide">
          {t("vizuMultilevel.levelRange")}
        </span>
        <h2 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">{t("vizuMultilevel.heroTitle")}</h2>
        <p className="mt-2 max-w-2xl text-white/80">{t("vizuMultilevel.heroBody")}</p>

        <div className="mt-6">
          <Button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
            size="lg"
            className="!bg-white !text-brand-900 hover:!bg-white/90"
          >
            {startMutation.isPending ? t("common.loading") : t("common.starten")}
            <span aria-hidden="true">→</span>
          </Button>
        </div>
      </motion.section>

      {/* How it works */}
      <section>
        <h2 className="mb-5 text-base font-bold text-text-primary">{t("vizuMultilevel.howItWorks")}</h2>
        <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {VIZU_MULTILEVEL_SKILLS.map((s) => {
            const Icon = s.icon;
            return (
              <motion.div
                key={s.skill}
                variants={cardEntrance}
                className="rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
              >
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow ${s.color}`}>
                  <Icon size={18} />
                </div>
                <p className="mt-3 font-semibold text-text-primary">{t(s.labelKey)}</p>
                <p className="mt-1 flex items-center gap-1.5 text-xs text-text-muted">
                  <Clock3 size={12} /> {t("vizuMultilevel.minutesEach")}
                </p>
              </motion.div>
            );
          })}
        </motion.div>
        <p className="mt-4 text-sm text-text-secondary">{t("vizuMultilevel.totalDuration")}</p>
      </section>

      {/* History */}
      <section>
        <h2 className="mb-5 text-base font-bold text-text-primary">{t("vizuMultilevel.historyTitle")}</h2>

        {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

        {!isLoading && (attempts?.length ?? 0) === 0 && (
          <div className="rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
            <Award size={32} className="mx-auto text-text-muted" />
            <p className="mt-3 text-sm text-text-secondary">{t("vizuMultilevel.historyEmpty")}</p>
          </div>
        )}

        {!isLoading && (attempts?.length ?? 0) > 0 && (
          <div className="space-y-3">
            {attempts!.map((attempt) => (
              <div
                key={attempt.id}
                className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
              >
                <div>
                  <p className="font-semibold text-text-primary">
                    {new Date(attempt.started_at).toLocaleDateString()}
                  </p>
                  <p className="mt-0.5 text-sm text-text-secondary">
                    {attempt.status === "COMPLETED" ? t("vizuMultilevel.statusCompleted") : t("vizuMultilevel.statusInProgress")}
                    {" · "}
                    {attempt.status === "COMPLETED"
                      ? (attempt.overall_level ?? t("vizuMultilevel.pendingReview"))
                      : t("vizuMultilevel.resultsPending")}
                  </p>
                </div>

                {attempt.status === "COMPLETED" ? (
                  <Button variant="secondary" size="sm" onClick={() => router.push(`/vizu-multilevel/${attempt.id}/natijalar`)}>
                    {t("vizuMultilevel.viewResults")}
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => router.push(`/vizu-multilevel/${attempt.id}/lesen`)}
                  >
                    <PlayCircle size={15} />
                    {t("vizuMultilevel.continueAttempt")}
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
