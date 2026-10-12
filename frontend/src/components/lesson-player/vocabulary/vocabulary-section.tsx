"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Languages, Search } from "lucide-react";

import { getLessonQuizzes } from "@/features/lessons/services/quiz-service";
import { completeLessonVocabulary, getLessonVocabularies } from "@/features/lessons/services/vocabulary-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import ExerciseSets, { useExercises } from "../skill-test/exercise-sets";
import VocabularyQuizSection from "./vocabulary-quiz-section";

/** Wortschatz: the lesson's words (from the course book) with a search,
 * then the server-graded practice sets. Lessons that still only have the
 * legacy VOCABULARY quiz keep it; a word list without any practice counts
 * as done once opened. */
export default function VocabularySection({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const marked = useRef(false);

  const { data: words, isLoading } = useQuery({ queryKey: ["lesson-vocabularies", lessonId], queryFn: () => getLessonVocabularies(lessonId) });
  const { data: sets, isLoading: setsLoading } = useExercises(lessonId, "wortschatz");
  const { data: legacy, isLoading: legacyLoading } = useQuery({
    queryKey: ["lesson-quizzes", lessonId, "VOCABULARY"],
    queryFn: () => getLessonQuizzes(lessonId, "VOCABULARY"),
    enabled: !setsLoading && (sets?.length ?? 0) === 0,
  });

  const sorted = useMemo(() => [...(words ?? [])].sort((a, b) => a.order_index - b.order_index), [words]);
  const shown = useMemo(() => {
    const q = query.trim().toLocaleLowerCase("de");
    if (!q) return sorted;
    return sorted.filter((w) => `${w.article ?? ""} ${w.german_word} ${w.plural ?? ""} ${w.translation}`.toLocaleLowerCase("de").includes(q));
  }, [sorted, query]);

  const hasSets = (sets?.length ?? 0) > 0;
  const hasLegacy = !hasSets && (legacy?.length ?? 0) > 0;
  const loading = isLoading || setsLoading || (!hasSets && legacyLoading);

  useEffect(() => {
    if (marked.current || loading || hasSets || hasLegacy || sorted.length === 0) return;
    marked.current = true;
    completeLessonVocabulary(lessonId)
      .then(() => queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] }))
      .catch(() => undefined);
  }, [loading, hasSets, hasLegacy, sorted.length, lessonId, queryClient]);

  return (
    <div className="space-y-6">
      <LessonSection title={t("lessons.sectionVocabulary")} description={t("lessons.vocabularyDescription")} icon={Languages}>
        {loading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

        {!loading && sorted.length === 0 && !hasSets && (
          <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
            <p className="text-text-secondary">{t("lessons.vocabularyEmpty")}</p>
          </div>
        )}

        {sorted.length > 0 && (
          <div className="space-y-4" data-testid="vocabulary-list">
            <div className="relative max-w-sm">
              <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t("lessons.vocabularySearch")}
                className="min-h-11 w-full rounded-xl bg-surface-hover/50 pl-9 pr-3 text-sm text-text-primary outline-none ring-1 ring-surface-border focus:ring-2 focus:ring-accent-blue"
                aria-label={t("lessons.vocabularySearch")}
              />
            </div>
            <p className="text-xs text-text-muted">{t("lessons.vocabularyCount", { n: sorted.length })}</p>
            <ul className="grid gap-2 sm:grid-cols-2">
              {shown.map((w) => (
                <li key={w.id} className="flex items-start justify-between gap-3 rounded-xl bg-surface-hover/50 px-3.5 py-2.5 ring-1 ring-surface-border">
                  <span className="min-w-0 text-[15px] text-text-primary">
                    {w.article && <span className="mr-1 text-text-muted">{w.article}</span>}
                    <span className="font-semibold">{w.german_word}</span>
                    {w.plural && <span className="ml-1 text-xs text-text-muted">(Pl. {w.plural})</span>}
                    {w.example_sentence && <span className="mt-0.5 block text-xs italic text-text-secondary">{w.example_sentence}</span>}
                  </span>
                  <span className="shrink-0 text-right text-sm text-text-secondary">{w.translation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {hasSets && (
          <div className="mt-10 space-y-3">
            <h3 className="text-base font-bold uppercase tracking-wide text-text-muted">{t("lessons.vocabularyPractice")}</h3>
            <ExerciseSets lessonId={lessonId} skill="wortschatz" sets={sets!} />
          </div>
        )}
      </LessonSection>

      {hasLegacy && <VocabularyQuizSection lessonId={lessonId} />}
    </div>
  );
}
