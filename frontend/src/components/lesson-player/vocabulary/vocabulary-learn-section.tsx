"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Library } from "lucide-react";

import { completeLessonVocabulary, getLessonVocabularies } from "@/features/lessons/services/vocabulary-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
}

/** A1's Wortschatz *learning* step — simple word-by-word browsing (Deutsch /
 * Übersetzung / Artikel / Plural / Beispiel), separate from the Wortschatz
 * Quiz (see vocabulary-quiz-section.tsx). Finishing here calls
 * completeLessonVocabulary(lessonId) with NO percentage — sets only
 * StudentProgress.vocabulary_completed, which is exactly what unlocks the
 * Quiz (server-side gate: grading_service.grade_and_submit). The Quiz
 * itself is the one that later sets vocabulary_score. */
export default function VocabularyLearnSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: words, isLoading } = useQuery({
    queryKey: ["lesson-vocabularies", lessonId],
    queryFn: () => getLessonVocabularies(lessonId),
  });

  const [index, setIndex] = useState(0);
  const [finished, setFinished] = useState(false);

  const completeMutation = useMutation({
    mutationFn: () => completeLessonVocabulary(lessonId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] });
    },
  });

  const total = words?.length ?? 0;
  const current = words?.[index];
  const isLast = index === total - 1;

  function goBack() {
    setIndex((i) => Math.max(0, i - 1));
  }

  function goNext() {
    if (!isLast) {
      setIndex((i) => Math.min(total - 1, i + 1));
      return;
    }
    setFinished(true);
    completeMutation.mutate();
  }

  return (
    <LessonSection
      title={t("lessons.sectionVocabulary")}
      description={finished ? "Abgeschlossen" : `Wort ${Math.min(index + 1, total)} / ${total}`}
      icon={Library}
    >
      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {!isLoading && total === 0 && (
        <p className="rounded-2xl bg-surface-hover p-6 text-center text-sm text-text-secondary">
          Für diese Lektion sind noch keine Vokabeln verfügbar.
        </p>
      )}

      {!isLoading && total > 0 && !finished && current && (
        <div className="space-y-5">
          <div className="flex items-center justify-between text-xs font-medium text-text-muted">
            <span>
              {index + 1} / {total} gelernt
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-hover">
            <div
              className="h-full rounded-full bg-accent-blue transition-all duration-300"
              style={{ width: `${((index + 1) / total) * 100}%` }}
            />
          </div>

          <div className="rounded-2xl bg-surface-hover/60 p-8 text-center ring-1 ring-surface-border">
            <p className="text-3xl font-bold text-text-primary">
              {current.article ? `${current.article} ` : ""}
              {current.german_word}
            </p>
            <p className="mt-2 text-lg text-text-secondary">{current.translation}</p>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-4 text-sm text-text-muted">
              {current.article && (
                <span>
                  Artikel: <span className="font-medium text-text-secondary">{current.article}</span>
                </span>
              )}
              {current.plural && (
                <span>
                  Plural: <span className="font-medium text-text-secondary">{current.plural}</span>
                </span>
              )}
            </div>

            {current.example_sentence && (
              <div className="mt-5 border-t border-surface-border pt-4 text-sm text-text-secondary">
                <p className="italic">{current.example_sentence}</p>
                {current.example_translation && (
                  <p className="mt-1 text-text-muted">{current.example_translation}</p>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={goBack}
              disabled={index === 0}
              className="inline-flex items-center gap-1.5 rounded-button px-4 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border transition enabled:hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ArrowLeft size={14} />
              Zurück
            </button>
            <button
              type="button"
              onClick={goNext}
              className="inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5"
            >
              {isLast ? "Abschließen" : "Weiter"}
              {!isLast && <ArrowRight size={14} />}
            </button>
          </div>
        </div>
      )}

      {finished && (
        <div className="rounded-2xl bg-surface-card p-6 text-center ring-1 ring-surface-border">
          <p className="text-sm font-medium text-success">✓ Wortschatz abgeschlossen</p>
          <p className="mt-1 text-sm text-text-secondary">{total} Wörter gelernt</p>
          <button
            type="button"
            onClick={() => router.push(`/lessons/${lessonId}/wortschatz-quiz`)}
            className="mt-5 inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-5 py-3 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition hover:-translate-y-0.5"
          >
            Zum Wortschatz Quiz
            <ArrowRight size={14} />
          </button>
        </div>
      )}
    </LessonSection>
  );
}
