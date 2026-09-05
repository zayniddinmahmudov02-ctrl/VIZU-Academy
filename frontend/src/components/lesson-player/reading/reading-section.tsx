"use client";

import { BookOpen } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getLessonReadings } from "@/features/lessons/services/reading-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
}

/** The real Lesen player — published Reading rows for this lesson (see
 * app/models/reading.py, admin/components/managers/reading-manager.tsx).
 * Legacy-backed on purpose: the Assessment Engine is no longer the
 * student-facing source for Lesen/Hören/Schreiben/Sprechen (see
 * backend/app/services/lesson_progress/section_gate.py's module
 * docstring) — this and its three siblings are the source of truth
 * again, same simple publish-gated content type Grammatik already uses. */
export default function ReadingSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: items, isLoading } = useQuery({
    queryKey: ["lesson-readings", lessonId],
    queryFn: () => getLessonReadings(lessonId),
  });

  return (
    <LessonSection title={t("lessons.sectionReading")} description={t("lessons.readingDescription")} icon={BookOpen}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">Für diese Lektion sind noch keine Texte verfügbar.</p>
        </div>
      )}

      <div className="space-y-5">
        {items?.map((item) => (
          <div key={item.id} className="rounded-2xl bg-surface-hover p-6">
            <h3 className="text-lg font-bold text-text-primary">{item.title}</h3>
            <div
              className="prose-editor mt-2.5 text-sm text-text-secondary sm:text-base"
              dangerouslySetInnerHTML={{ __html: item.content }}
            />
          </div>
        ))}
      </div>
    </LessonSection>
  );
}
