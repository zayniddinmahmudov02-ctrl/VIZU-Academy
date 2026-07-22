"use client";

import { Languages } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

export default function GrammarSection() {
  const { t } = useTranslation();

  return (
    <LessonSection
      title={t("lessons.sectionGrammar")}
      description={t("lessons.grammarDescription")}
      icon={Languages}
    >
      <div className="space-y-5">
        <div className="rounded-2xl bg-surface-hover p-6">
          <h3 className="text-lg font-bold text-text-primary">{t("lessons.grammarTopicTitle")}</h3>
          <p className="mt-2.5 text-sm text-text-secondary sm:text-base">
            ich • du • er • sie • es • wir • ihr • Sie
          </p>
        </div>

        <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border">
          <h3 className="font-bold text-text-primary">{t("lessons.grammarExampleLabel")}</h3>
          <div className="mt-3 space-y-2 text-sm text-text-secondary sm:text-base">
            <p>Ich bin Student.</p>
            <p>Du bist Lehrer.</p>
            <p>Er ist Arzt.</p>
          </div>
        </div>
      </div>
    </LessonSection>
  );
}
