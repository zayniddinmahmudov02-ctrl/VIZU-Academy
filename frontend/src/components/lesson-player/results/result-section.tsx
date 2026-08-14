"use client";

import { useQuery } from "@tanstack/react-query";
import { Trophy } from "lucide-react";

import { getMyLessonScore } from "@/features/lessons/services/lesson-score-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";
import LessonScoreBreakdown from "./lesson-score-breakdown";

interface Props {
  lessonId: string;
}

/** "Lektion X — Fortschritt/Punktzahl/Breakdown/Feedback/Stärken/Noch
 * üben/Lesson Quiz" — computed live from real progress/quiz/assessment
 * data (see LessonScoringService), never a static placeholder. */
export default function ResultSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: score, isLoading } = useQuery({
    queryKey: ["lesson-score", lessonId],
    queryFn: () => getMyLessonScore(lessonId),
  });

  return (
    <LessonSection title={t("lessons.sectionResults")} description="Deine Ergebnisse für diese Lektion." icon={Trophy}>
      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}
      {!isLoading && score && <LessonScoreBreakdown score={score} />}
    </LessonSection>
  );
}
