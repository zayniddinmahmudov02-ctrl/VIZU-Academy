"use client";

import { PenSquare } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getLessonWritings, wordRange, type WritingCompetency } from "@/features/lessons/services/writing-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import WritingTaskPanel from "./writing-task-panel";

interface Props {
  lessonId: string;
  /** whose written tasks: Schreiben (default) or the written tasks of Wortschatz / Grammatik / Lesen */
  competency?: WritingCompetency;
}

const TITLES: Record<WritingCompetency, [string, string]> = {
  SCHREIBEN: ["lessons.sectionWriting", "lessons.writingDescription"],
  WORTSCHATZ: ["lessons.wortschatzTasks", "lessons.wortschatzTasksDescription"],
  GRAMMATIK: ["lessons.grammatikTasks", "lessons.grammatikTasksDescription"],
  LESEN: ["lessons.lesenTasks", "lessons.lesenTasksDescription"],
};

/** Written tasks of one competency — published Writing rows of this lesson
 * (app/models/writing.py, `competency`), each with a writing panel
 * (WritingTaskPanel — textarea, ÄÖÜß insertion, word/char count, draft/
 * submit, analysis, history) backed by StudentWriting. Schreiben shows only
 * Schreiben tasks; a Wortschatz worksheet, a Grammatik written exercise or the
 * open questions on a Lesen text appear only on their own competency page,
 * which renders this section with its `competency` (hidden when it has none). */
export default function WritingSection({ lessonId, competency = "SCHREIBEN" }: Props) {
  const { t } = useTranslation();

  const { data: items, isLoading } = useQuery({
    queryKey: ["lesson-writings", lessonId, competency],
    queryFn: () => getLessonWritings(lessonId, competency),
  });

  if (competency !== "SCHREIBEN" && !isLoading && (items?.length ?? 0) === 0) return null;

  const [title, description] = TITLES[competency];
  return (
    <div data-testid="writing-section" data-competency={competency}>
      <LessonSection title={t(title)} description={t(description)} icon={PenSquare}>
        {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

        {!isLoading && (items?.length ?? 0) === 0 && (
          <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
            <p className="text-text-secondary">Für diese Lektion ist noch keine Schreibaufgabe verfügbar.</p>
          </div>
        )}

        <div className="space-y-5">
          {items?.map((item) => (
            <div key={item.id} className="rounded-2xl bg-surface-hover p-4 sm:p-6" data-testid="writing-task" data-title={item.title}>
              <h3 className="text-lg font-bold text-text-primary">{item.title}</h3>
              <p className="mt-2.5 whitespace-pre-line break-words text-sm text-text-secondary sm:text-base">{item.instruction}</p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-text-muted">
                {item.text_type && competency === "SCHREIBEN" && (
                  <span className="rounded-full bg-surface-card px-2.5 py-1 font-semibold ring-1 ring-surface-border">
                    {t(`lessons.textType_${item.text_type}`)}
                  </span>
                )}
                {item.audience && (
                  <span className="rounded-full bg-surface-card px-2.5 py-1 ring-1 ring-surface-border">
                    {t("lessons.writingAudience")}: {item.audience}
                  </span>
                )}
                {wordRange(item.min_words, item.max_words) && (
                  <span className="rounded-full bg-surface-card px-2.5 py-1 ring-1 ring-surface-border">
                    {t("lessons.writingWordsRange", { range: wordRange(item.min_words, item.max_words) ?? "" })}
                  </span>
                )}
                {item.time_limit_minutes && (
                  <span className="rounded-full bg-surface-card px-2.5 py-1 ring-1 ring-surface-border">
                    {t("lessons.writingTimeLimit", { n: item.time_limit_minutes })}
                  </span>
                )}
              </div>
              <WritingTaskPanel writing={item} />
            </div>
          ))}
        </div>
      </LessonSection>
    </div>
  );
}
