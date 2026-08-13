"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Library, Volume2 } from "lucide-react";
import { motion } from "framer-motion";

import { getLessonVocabularies } from "@/features/lessons/services/vocabulary-service";
import { cardEntrance, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
}

/** Real Wortschatz panel — published Vocabulary rows for this lesson (see
 * app/models/vocabulary.py). Requires the lesson's video to be completed
 * first, enforced server-side (GET /vocabularies/lesson/{id}). */
export default function VocabularySection({ lessonId }: Props) {
  const { t } = useTranslation();
  const [learned, setLearned] = useState<Set<string>>(new Set());

  const { data: words, isLoading } = useQuery({
    queryKey: ["lesson-vocabularies", lessonId],
    queryFn: () => getLessonVocabularies(lessonId),
  });

  function toggleLearned(id: string) {
    setLearned((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <LessonSection title={t("lessons.sectionVocabulary")} description={t("lessons.vocabularyDescription")} icon={Library}>
      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {!isLoading && (words?.length ?? 0) === 0 && (
        <p className="rounded-2xl bg-surface-hover p-6 text-center text-sm text-text-secondary">
          Für diese Lektion sind noch keine Inhalte verfügbar.
        </p>
      )}

      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-3">
        {words?.map((word) => {
          const isLearned = learned.has(word.id);
          return (
            <motion.div
              key={word.id}
              variants={cardEntrance}
              onClick={() => toggleLearned(word.id)}
              className={`cursor-pointer rounded-2xl border p-5 transition-all duration-200 ${
                isLearned
                  ? "border-success/40 bg-success/5"
                  : "border-surface-border bg-surface-hover hover:border-accent-blue/30"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-lg font-bold text-text-primary">
                    {word.article && <span className="text-text-secondary">{word.article} </span>}
                    {word.german_word}
                  </p>
                  <p className="mt-1 text-sm text-text-secondary">{word.translation}</p>
                  {word.example_sentence && (
                    <p className="mt-2 text-sm italic text-text-muted">{word.example_sentence}</p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {word.audio_url && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        new Audio(word.audio_url!).play();
                      }}
                      className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-card text-accent-blue ring-1 ring-surface-border"
                      aria-label="Aussprache abspielen"
                    >
                      <Volume2 size={15} />
                    </button>
                  )}
                  {isLearned && (
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-success/15 text-success">
                      <Check size={15} />
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </LessonSection>
  );
}
