"use client";

import { PenSquare } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getLessonWritings } from "@/features/lessons/services/writing-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
}

/** The real Schreiben panel — published Writing rows for this lesson
 * (see app/models/writing.py, admin/components/managers/writing-
 * manager.tsx). Legacy-backed on purpose, same as its Lesen/Hören/
 * Sprechen siblings — see reading-section.tsx's docstring. View-only:
 * the legacy schema has no wired submission/grading pipeline (unlike
 * the Assessment Engine's WritingSubmission flow) — building one is a
 * separate feature, not part of this switch back to legacy content. */
export default function WritingSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: items, isLoading } = useQuery({
    queryKey: ["lesson-writings", lessonId],
    queryFn: () => getLessonWritings(lessonId),
  });

  return (
    <LessonSection title={t("lessons.sectionWriting")} description={t("lessons.writingDescription")} icon={PenSquare}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">Für diese Lektion ist noch keine Schreibaufgabe verfügbar.</p>
        </div>
      )}

      <div className="space-y-5">
        {items?.map((item) => (
          <div key={item.id} className="rounded-2xl bg-surface-hover p-6">
            <h3 className="text-lg font-bold text-text-primary">{item.title}</h3>
            <p className="mt-2.5 whitespace-pre-line text-sm text-text-secondary sm:text-base">{item.instruction}</p>
            {(item.min_words != null || item.max_words != null) && (
              <p className="mt-3 text-xs text-text-muted">
                {item.min_words ?? 0}–{item.max_words ?? "∞"} Wörter
              </p>
            )}
          </div>
        ))}
      </div>
    </LessonSection>
  );
}
