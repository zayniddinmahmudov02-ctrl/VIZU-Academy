"use client";

import { useEffect, useState } from "react";
import { Mic } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getPublicLessonAssessment, startAttempt } from "@/features/admin/services/assessment-service";
import type { PublicSection, PublicTask } from "@/features/admin/types/assessment.types";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import SprechenTask from "./sprechen-task";

interface Props {
  lessonId: string;
}

/** The real Sprechen player, backed by the universal Assessment engine
 * (Assessment[type=COURSE] -> Section[skill=SPRECHEN] -> Task[SPEAKING]).
 * Previously this slot always rendered the same hardcoded generic
 * recording prompt via WritingEditor-style MediaRecorder code that posted
 * to a nonexistent /speakings/evaluate endpoint (confirmed dead in
 * research — the endpoint 404s). That component's files are left
 * untouched but now unused; this renders genuinely published,
 * admin-authored tasks with real backend storage, or the required empty
 * state — never a demo task. */
export default function SpeakingSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: assessment, isLoading } = useQuery({
    queryKey: ["public-lesson-assessment", lessonId],
    queryFn: () => getPublicLessonAssessment(lessonId),
  });

  const sections = (assessment?.sections ?? []).filter((s: PublicSection) => s.skill === "SPRECHEN");
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
    <LessonSection title={t("lessons.sectionSpeaking")} description={t("lessons.speakingDescription")} icon={Mic}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && !hasContent && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">Für diese Lektion ist noch keine Sprechaufgabe verfügbar.</p>
        </div>
      )}

      {!isLoading && hasContent && !attemptId && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && hasContent && attemptId && (
        <div className="space-y-6">
          {allTasks.map((task: PublicTask) => (
            <SprechenTask
              key={task.id}
              task={task}
              attemptId={attemptId}
              locked={attemptLocked}
              allowResubmit={assessment!.allow_resubmit}
            />
          ))}
        </div>
      )}
    </LessonSection>
  );
}
