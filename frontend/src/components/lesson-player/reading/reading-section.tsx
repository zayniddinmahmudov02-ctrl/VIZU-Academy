"use client";

import { BookOpen } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

export default function ReadingSection() {
  const { t } = useTranslation();

  return (
    <LessonSection
      title={t("lessons.sectionReading")}
      description={t("lessons.readingDescription")}
      icon={BookOpen}
    >
      <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border sm:p-8">
        <h3 className="text-xl font-bold text-text-primary">Hallo!</h3>

        <p className="mt-5 leading-8 text-text-secondary">
          Hallo!
          <br />
          Ich heiße Anna.
          <br />
          Ich komme aus Deutschland.
          <br />
          Ich wohne in Berlin.
          <br />
          Ich lerne Deutsch.
        </p>
      </div>
    </LessonSection>
  );
}
