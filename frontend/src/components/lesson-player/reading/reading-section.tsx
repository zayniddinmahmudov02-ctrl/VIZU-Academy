"use client";

import { BookOpen } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getLesenTest, reviewLesen, startLesen, submitLesen } from "@/features/lessons/services/lesson-skills-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import SkillTest from "../skill-test/skill-test";

interface Props {
  lessonId: string;
}

/** Lesen: every published text of the lesson with its questions, as one
 * server-graded test (see backend app/api/lesson_skills/router.py). Each
 * text is shown with its own questions right below it. */
export default function ReadingSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["lesen-test", lessonId],
    queryFn: () => getLesenTest(lessonId),
  });

  const texts = data?.texts ?? [];

  return (
    <LessonSection title={t("lessons.sectionReading")} description={t("lessons.readingDescription")} icon={BookOpen}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}
      {isError && <p className="text-sm text-danger">{t("lessons.loadError")}</p>}

      {!isLoading && !isError && texts.length === 0 && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">{t("lessons.lesenEmpty")}</p>
        </div>
      )}

      {data && texts.length > 0 && (
        <SkillTest
          testId="lesen-test"
          sections={texts.map((text) => ({
            id: text.id,
            questions: text.questions,
            header: (
              <article className="rounded-2xl bg-surface-hover p-5 sm:p-6" data-testid="lesen-text">
                <h3 className="text-lg font-bold text-text-primary">{text.title}</h3>
                <div
                  className="prose-editor mt-2.5 text-[15px] leading-relaxed text-text-primary sm:text-base"
                  dangerouslySetInnerHTML={{ __html: text.content }}
                />
              </article>
            ),
          }))}
          summary={data.summary}
          attempts={data.attempts}
          start={() => startLesen(lessonId)}
          submit={(attemptId, answers) => submitLesen(lessonId, attemptId, answers)}
          review={(attemptId) => reviewLesen(lessonId, attemptId)}
          invalidate={[["lesen-test", lessonId], ["lesson-skill-results", lessonId], ["lesson-score", lessonId]]}
        />
      )}
    </LessonSection>
  );
}
