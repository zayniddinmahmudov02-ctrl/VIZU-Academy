"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Award, Trophy } from "lucide-react";

import Button from "@/components/ui/button";
import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MOCK_SKILLS } from "@/features/vizu-mock/constants/skills";
import { completeVizuMockAttempt, getVizuMockAttempt } from "@/features/vizu-mock/services/vizu-mock-service";
import type { VizuMockAttempt } from "@/features/vizu-mock/types/vizu-mock.types";

const SKILL_LEVEL_KEY: Record<string, keyof VizuMockAttempt> = {
  lesen: "lesen_level",
  hoeren: "hoeren_level",
  schreiben: "schreiben_level",
  sprechen: "sprechen_level",
};

/** Results step — marks the attempt COMPLETED (once) and shows the
 * per-skill + overall level. Every level is null today (no scoring
 * algorithm exists yet, per spec), so this renders the real "not yet
 * evaluated" placeholder state rather than a fabricated level. */
export default function VizuMockResultsPage() {
  const { t } = useTranslation();
  const { attemptId } = useParams<{ attemptId: string }>();
  const queryClient = useQueryClient();
  const completedOnce = useRef(false);

  const { data: attempt, isLoading } = useQuery({
    queryKey: ["vizu-mock-attempt", attemptId],
    queryFn: () => getVizuMockAttempt(attemptId),
  });

  const completeMutation = useMutation({
    mutationFn: () => completeVizuMockAttempt(attemptId),
    onSuccess: (updated) => {
      queryClient.setQueryData(["vizu-mock-attempt", attemptId], updated);
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-attempts"] });
    },
  });

  useEffect(() => {
    if (attempt && attempt.status === "IN_PROGRESS" && !completedOnce.current) {
      completedOnce.current = true;
      completeMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt]);

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <PageHeader icon={Trophy} titleKey="vizuMock.resultsTitle" gradient="from-accent-blue to-accent-purple" />

      {(isLoading || completeMutation.isPending) && (
        <p className="text-center text-sm text-text-secondary">{t("common.loading")}</p>
      )}

      {attempt && !isLoading && (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            {VIZU_MOCK_SKILLS.map((s) => {
              const Icon = s.icon;
              const level = attempt[SKILL_LEVEL_KEY[s.skill]] as string | null;
              return (
                <div
                  key={s.skill}
                  className="flex items-center gap-4 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
                >
                  <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow ${s.color}`}>
                    <Icon size={18} />
                  </div>
                  <div>
                    <p className="font-semibold text-text-primary">{t(s.labelKey)}</p>
                    <p className="text-sm text-text-muted">{level ?? t("vizuMock.resultsPending")}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-8 text-center text-white shadow-[var(--shadow-lg)]">
            <p className="text-sm font-semibold uppercase tracking-wide text-white/70">
              {t("vizuMock.resultsOverall")}
            </p>
            <p className="mt-2 text-4xl font-extrabold">{attempt.overall_level ?? "—"}</p>
            {!attempt.overall_level && <p className="mt-3 text-sm text-white/70">{t("vizuMock.resultsPendingNote")}</p>}
          </div>

          <div className="flex flex-wrap justify-center gap-3">
            <Link href={`/vizu-mock/${attemptId}/sertifikat`}>
              <Button variant="secondary">
                <Award size={16} />
                {t("vizuMock.viewCertificate")}
              </Button>
            </Link>
            <Link href="/vizu-mock">
              <Button variant="ghost">{t("vizuMock.backToHub")}</Button>
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
