"use client";

import { Headphones } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import SkillAssessmentSection from "../common/skill-assessment-section";

interface Props {
  lessonId: string;
}

/** The real Hören player, backed by the universal Assessment engine
 * (Assessment[type=COURSE] -> Section[skill=HOEREN] -> Task -> Question ->
 * Option), reusing the exact same engine/component as ReadingSection —
 * no duplicated task engine, per spec. Previously this read `lesson.audioUrl`,
 * a frontend field the backend Lesson model never actually populated (no
 * `audio_url` column exists on it), so it always rendered the empty state
 * regardless of any real content — dead functionality, safe to replace. */
export default function ListeningSection({ lessonId }: Props) {
  const { t } = useTranslation();
  return (
    <SkillAssessmentSection
      lessonId={lessonId}
      skill="HOEREN"
      title={t("lessons.sectionListening")}
      description={t("lessons.listeningDescription")}
      icon={Headphones}
      emptyStateText="Für diese Lektion sind noch keine Hörübungen verfügbar."
    />
  );
}
