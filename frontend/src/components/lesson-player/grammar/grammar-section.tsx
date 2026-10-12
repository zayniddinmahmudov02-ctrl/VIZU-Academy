"use client";

import { useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BookMarked } from "lucide-react";

import { completeLessonGrammar, getLessonGrammars } from "@/features/lessons/services/grammar-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import ExerciseSets, { useExercises } from "../skill-test/exercise-sets";

/** Grammatik: the lesson's rules (from the course book) followed by the
 * auto-graded grammar exercises. A lesson with rules but no exercises
 * counts as done once the rules have been opened. */
export default function GrammarSection({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { data: rules, isLoading } = useQuery({ queryKey: ["lesson-grammars", lessonId], queryFn: () => getLessonGrammars(lessonId) });
  const { data: sets, isLoading: setsLoading } = useExercises(lessonId, "grammatik");
  const marked = useRef(false);

  const hasRules = (rules?.length ?? 0) > 0;
  const hasSets = (sets?.length ?? 0) > 0;

  useEffect(() => {
    if (marked.current || isLoading || setsLoading || !hasRules || hasSets) return;
    marked.current = true;
    completeLessonGrammar(lessonId)
      .then(() => queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] }))
      .catch(() => undefined);
  }, [hasRules, hasSets, isLoading, setsLoading, lessonId, queryClient]);

  return (
    <LessonSection title={t("lessons.sectionGrammar")} description={t("lessons.grammarDescription")} icon={BookMarked}>
      {(isLoading || setsLoading) && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && !setsLoading && !hasRules && !hasSets && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">{t("lessons.grammarEmpty")}</p>
        </div>
      )}

      <div className="space-y-10">
        {hasRules && (
          <div className="space-y-5" data-testid="grammar-rules">
            {rules!.map((rule) => (
              <article key={rule.id} className="rounded-2xl bg-surface-hover p-5 sm:p-6">
                <h3 className="text-lg font-bold text-text-primary">{rule.title}</h3>
                {/<[a-z][\s\S]*>/i.test(rule.content) ? (
                  // sanitized on the server (app/core/utils/safe_html.py)
                  <div className="prose-editor mt-2 text-[15px] leading-relaxed text-text-primary" dangerouslySetInnerHTML={{ __html: rule.content }} />
                ) : (
                  <p className="mt-2 whitespace-pre-line text-[15px] leading-relaxed text-text-primary">{rule.content}</p>
                )}
              </article>
            ))}
          </div>
        )}

        {hasSets && (
          <div className="space-y-3">
            <h3 className="text-base font-bold uppercase tracking-wide text-text-muted">{t("lessons.grammarExercises")}</h3>
            <ExerciseSets lessonId={lessonId} skill="grammatik" sets={sets!} />
          </div>
        )}
      </div>
    </LessonSection>
  );
}
