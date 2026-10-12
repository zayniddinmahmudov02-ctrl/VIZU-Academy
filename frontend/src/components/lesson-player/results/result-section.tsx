"use client";

import { CheckCircle2, Trophy } from "lucide-react";

import { COMPLETION_TRACKED_GATE_KEYS } from "@/constants/lesson-sections";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";
import SectionProgressionList from "./section-progression-list";
import SkillResultsPanel from "./skill-results-panel";

interface Props {
  lessonId: string;
}

/** "Lektion X — Fortschritt/Punktzahl/Breakdown/Feedback/Stärken/Noch
 * üben/Lesson Quiz" — computed live from real progress/quiz/assessment
 * data (see LessonScoringService), never a static placeholder. Shows
 * "Lektion abgeschlossen ✓" once every required section (up through
 * Yakuniy Test) is done. */
export default function ResultSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const isLoading = false;
  const { data: gate, isLoading: gateLoading } = useSectionGate(lessonId);

  // Lesson completed = every applicable step that has a completion signal
  // is done (Schreiben/Sprechen only once a teacher has graded them).
  const tracked = gate ? COMPLETION_TRACKED_GATE_KEYS.filter((key) => gate[key]?.applicable) : [];
  const allDone = gate ? tracked.length > 0 && tracked.every((key) => gate[key].completed) : false;

  return (
    <LessonSection title={t("lessons.sectionResults")} description={t("lessons.resultsDescription")} icon={Trophy}>
      {(isLoading || gateLoading) && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {!isLoading && !gateLoading && (
        <div className="space-y-6">
          {allDone && (
            <div className="flex items-center gap-2 rounded-2xl bg-success/10 px-5 py-4 text-success">
              <CheckCircle2 size={20} />
              <span className="text-base font-bold">{t("lessons.lessonCompleted")}</span>
            </div>
          )}

          <SkillResultsPanel lessonId={lessonId} />
          {gate && <SectionProgressionList gate={gate} />}
          {/* the lesson result is SkillResultsPanel (proportional, interim
              until every required skill is graded); the legacy 100-point
              breakdown stays in the admin per-student view only */}
        </div>
      )}
    </LessonSection>
  );
}
