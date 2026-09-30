"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Award, Clock3, Gauge, PlayCircle } from "lucide-react";

import Button from "@/components/ui/button";
import PageHeader from "@/components/dashboard/page-header";
import { cardEntrance, fadeInUp, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MOCK_SKILLS } from "@/features/vizu-mock/constants/skills";
import { createVizuMockAttempt, listVizuMockAttempts } from "@/features/vizu-mock/services/vizu-mock-service";

export default function VizuMockHubPage() {
  const { t } = useTranslation();
  const router = useRouter();

  const { data: attempts, isLoading } = useQuery({
    queryKey: ["vizu-mock-attempts"],
    queryFn: listVizuMockAttempts,
  });

  const startMutation = useMutation({
    mutationFn: createVizuMockAttempt,
    onSuccess: (attempt) => router.push(`/vizu-mock/${attempt.id}/lesen`),
  });

  return (
    <div className="space-y-10">
      <PageHeader icon={Gauge} titleKey="vizuMock.title" subtitleKey="vizuMock.subtitle" gradient="from-accent-blue to-accent-purple" />

      {/* Hero */}
      <motion.section
        variants={fadeInUp}
        initial="hidden"
        animate="show"
        className="relative overflow-hidden rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-6 text-white shadow-[var(--shadow-lg)] sm:p-8"
      >
        <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">{t("vizuMock.heroTitle")}</h2>
        <p className="mt-2 max-w-2xl text-white/80">{t("vizuMock.heroBody")}</p>

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
        <h2 className="mb-5 text-base font-bold text-text-primary">{t("vizuMock.howItWorks")}</h2>
        <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {VIZU_MOCK_SKILLS.map((s) => {
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
                  <Clock3 size={12} /> {t("vizuMock.minutesEach")}
                </p>
              </motion.div>
            );
          })}
        </motion.div>
        <p className="mt-4 text-sm text-text-secondary">{t("vizuMock.totalDuration")}</p>
      </section>

      {/* History */}
      <section>
        <h2 className="mb-5 text-base font-bold text-text-primary">{t("vizuMock.historyTitle")}</h2>

        {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

        {!isLoading && (attempts?.length ?? 0) === 0 && (
          <div className="rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
            <Award size={32} className="mx-auto text-text-muted" />
            <p className="mt-3 text-sm text-text-secondary">{t("vizuMock.historyEmpty")}</p>
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
                    {attempt.status === "COMPLETED" ? t("vizuMock.statusCompleted") : t("vizuMock.statusInProgress")}
                    {" · "}
                    {attempt.overall_level ?? t("vizuMock.resultsPending")}
                  </p>
                </div>

                {attempt.status === "COMPLETED" ? (
                  <Button variant="secondary" size="sm" onClick={() => router.push(`/vizu-mock/${attempt.id}/natijalar`)}>
                    {t("vizuMock.viewResults")}
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => router.push(`/vizu-mock/${attempt.id}/lesen`)}
                  >
                    <PlayCircle size={15} />
                    {t("vizuMock.continueAttempt")}
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
