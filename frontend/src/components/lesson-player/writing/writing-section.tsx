"use client";

import { PenSquare } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";
import WritingEditor from "./writing-editor";

interface Props {
  lessonId: string;
  prompt?: string;
  targetLevel?: string;
}

export default function WritingSection({
  lessonId,
  prompt,
  targetLevel = "A1",
}: Props) {
  const { t } = useTranslation();

  const resolvedPrompt =
    prompt ??
    "Stell dich vor: Schreibe 5–8 Sätze auf Deutsch über dich, deine Familie und deine Hobbys.";

  return (
    <LessonSection
      title={t("lessons.sectionWriting")}
      description={t("lessons.writingDescription")}
      icon={PenSquare}
    >
      <WritingEditor prompt={resolvedPrompt} targetLevel={targetLevel} lessonId={lessonId} />
    </LessonSection>
  );
}
