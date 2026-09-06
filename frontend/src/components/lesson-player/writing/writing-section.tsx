"use client";

import { PenSquare } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getLessonWritings } from "@/features/lessons/services/writing-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import WritingTaskPanel from "./writing-task-panel";

interface Props {
  lessonId: string;
}

/** The real Schreiben panel — published Writing rows for this lesson
 * (see app/models/writing.py), each now paired with a real writing panel
 * (WritingTaskPanel — textarea, ÄÖÜß insertion, word/char count, draft/
 * submit) backed by StudentWriting (app/models/student_writing.py), a
 * table that already existed but had no real submission workflow wired
 * to it until now. Legacy-backed on purpose, same as its Lesen/Hören/
 * Sprechen siblings — see reading-section.tsx's docstring; only the
 * "view-only" half of that description no longer applies to this
 * section specifically. */
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
            <WritingTaskPanel writing={item} />
          </div>
        ))}
      </div>
    </LessonSection>
  );
}
