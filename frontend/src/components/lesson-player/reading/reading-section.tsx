"use client";

import { BookOpen } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import SkillAssessmentSection from "../common/skill-assessment-section";

interface Props {
  lessonId: string;
}

/** The real Lesen player, backed by the universal Assessment engine
 * (Assessment[type=COURSE] -> Section[skill=LESEN] -> Task -> Question ->
 * Option). Thin wrapper over SkillAssessmentSection, which is shared with
 * ListeningSection so the attempt-taking logic exists exactly once. */
export default function ReadingSection({ lessonId }: Props) {
  const { t } = useTranslation();
  return (
    <SkillAssessmentSection
      lessonId={lessonId}
      skill="LESEN"
      title={t("lessons.sectionReading")}
      description={t("lessons.readingDescription")}
      icon={BookOpen}
      emptyStateText="Für diese Lektion sind noch keine Aufgaben verfügbar."
    />
  );
}
