"use client";

import { GraduationCap } from "lucide-react";

import Loading from "@/components/common/loading";
import PageHeader from "@/components/dashboard/page-header";
import LmsErrorCard from "@/components/lms/lms-error-card";
import LmsLevelCard from "@/components/lms/lms-level-card";
import { useLmsLevels } from "@/features/lms/hooks/use-lms";

/** VIZU LMS — the five CEFR levels with the student's progress. Every count
 * (lessons per level, available, completed) comes from GET /lms/levels. */
export default function KursePageClient() {
  const { data, isLoading, error, refetch } = useLmsLevels();

  return (
    <div className="space-y-8">
      <PageHeader
        icon={GraduationCap}
        titleKey="lms.levelsTitle"
        subtitleKey="lms.levelsSubtitle"
        subtitleVars={{ count: data?.total_lessons_target ?? "…" }}
        gradient="from-accent-blue to-purple-600"
      />

      {isLoading && <Loading />}
      {error ? <LmsErrorCard error={error} onRetry={() => refetch()} /> : null}

      {data && (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3" data-testid="lms-levels">
          {data.levels.map((level) => (
            <LmsLevelCard key={level.level} level={level} />
          ))}
        </div>
      )}
    </div>
  );
}
