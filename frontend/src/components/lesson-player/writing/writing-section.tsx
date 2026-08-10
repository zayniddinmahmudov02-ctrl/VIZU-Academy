"use client";

import { useEffect, useState } from "react";
import { PenSquare } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getPublicLessonAssessment, startAttempt } from "@/features/admin/services/assessment-service";
import type { PublicSection, PublicTask } from "@/features/admin/types/assessment.types";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import SchreibenTask from "./schreiben-task";

interface Props {
  lessonId: string;
}

/** The real Schreiben player, backed by the universal Assessment engine
 * (Assessment[type=COURSE] -> Section[skill=SCHREIBEN] -> Task[WRITING]).
 * Previously this slot always showed the same hardcoded practice prompt
 * ("Stell dich vor: Schreibe 5–8 Sätze...") to every user regardless of
 * lesson — that generic tool (WritingEditor/useWritingEvaluation) is left
 * untouched and unused elsewhere; this renders genuinely published,
 * admin-authored tasks instead, or the required empty state. */
export default function WritingSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: assessment, isLoading } = useQuery({
    queryKey: ["public-lesson-assessment", lessonId],
    queryFn: () => getPublicLessonAssessment(lessonId),
  });

  const sections = (assessment?.sections ?? []).filter((s: PublicSection) => s.skill === "SCHREIBEN");
  const allTasks = sections.flatMap((s: PublicSection) => s.tasks);
  const hasContent = allTasks.length > 0;

  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [attemptLocked, setAttemptLocked] = useState(false);

  useEffect(() => {
    if (assessment && hasContent && !attemptId) {
      startAttempt(assessment.id).then((attempt) => {
        setAttemptId(attempt.id);
        setAttemptLocked(attempt.locked);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessment, hasContent]);

  return (
    <LessonSection title={t("lessons.sectionWriting")} description={t("lessons.writingDescription")} icon={PenSquare}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && !hasContent && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">Für diese Lektion ist noch keine Schreibaufgabe verfügbar.</p>
        </div>
      )}

      {!isLoading && hasContent && !attemptId && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && hasContent && attemptId && (
        <div className="space-y-6">
          {allTasks.map((task: PublicTask) => (
            <SchreibenTask
              key={task.id}
              task={task}
              attemptId={attemptId}
              locked={attemptLocked}
              allowEdit={assessment!.allow_edit}
              allowResubmit={assessment!.allow_resubmit}
            />
          ))}
        </div>
      )}
    </LessonSection>
  );
}
