"use client";

import { ClipboardCheck } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

export default function HomeworkSection() {
  const { t } = useTranslation();

  return (
    <LessonSection
      title={t("lessons.sectionHomework")}
      description={t("lessons.homeworkDescription")}
      icon={ClipboardCheck}
    >
      <div className="rounded-2xl bg-surface-hover p-6 sm:p-8">
        <h3 className="text-xl font-bold text-text-primary">{t("lessons.sectionHomework")}</h3>
        <p className="mt-3 text-text-secondary">{t("lessons.homeworkBody")}</p>
      </div>
    </LessonSection>
  );
}
