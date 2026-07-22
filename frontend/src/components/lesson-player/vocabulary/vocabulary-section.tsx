"use client";

import { useState } from "react";
import { Check, Library, Volume2 } from "lucide-react";
import { motion } from "framer-motion";

import { cardEntrance, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

const WORDS = [
  { article: "der", word: "Student", translation: "Talaba", example: "Der Student lernt Deutsch." },
  { article: "die", word: "Schule", translation: "Maktab", example: "Die Schule ist groß." },
  { article: "das", word: "Buch", translation: "Kitob", example: "Das Buch ist interessant." },
];

export default function VocabularySection() {
  const { t } = useTranslation();
  const [learned, setLearned] = useState<Set<string>>(new Set());

  function toggleLearned(word: string) {
    setLearned((prev) => {
      const next = new Set(prev);
      if (next.has(word)) {
        next.delete(word);
      } else {
        next.add(word);
      }
      return next;
    });
  }

  function playPronunciation(article: string, word: string) {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(`${article} ${word}`);
    utterance.lang = "de-DE";
    window.speechSynthesis.speak(utterance);
  }

  return (
    <LessonSection
      title={t("lessons.sectionVocabulary")}
      description={t("lessons.vocabularyDescription")}
      icon={Library}
    >
      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid gap-4">
        {WORDS.map((item) => {
          const isLearned = learned.has(item.word);

          return (
            <motion.div
              key={item.word}
              variants={cardEntrance}
              className={`rounded-2xl p-6 shadow-sm ring-1 transition-shadow hover:shadow-[var(--shadow-md)] ${
                isLearned ? "bg-success/5 ring-success/30" : "bg-surface-hover/60 ring-surface-border"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="rounded-lg bg-accent-blue px-3 py-1 text-sm font-semibold text-white">
                    {item.article}
                  </span>
                  <h3 className="mt-4 text-2xl font-bold text-text-primary sm:text-3xl">
                    {item.word}
                  </h3>
                </div>

                <div className="flex gap-2.5">
                  <button
                    type="button"
                    onClick={() => playPronunciation(item.article, item.word)}
                    aria-label={t("lessons.vocabularyPlayAudio")}
                    className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface-hover text-text-secondary transition-colors hover:bg-accent-blue/10 hover:text-accent-blue"
                  >
                    <Volume2 size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleLearned(item.word)}
                    aria-pressed={isLearned}
                    aria-label={isLearned ? t("lessons.vocabularyLearned") : t("lessons.vocabularyMarkLearned")}
                    className={`flex h-9 w-9 items-center justify-center rounded-lg transition-colors ${
                      isLearned
                        ? "bg-success/15 text-success"
                        : "bg-surface-hover text-text-secondary hover:bg-success/10 hover:text-success"
                    }`}
                  >
                    <Check size={16} />
                  </button>
                </div>
              </div>

              <p className="mt-4 text-lg font-semibold text-accent-blue">{item.translation}</p>
              <p className="mt-2 text-text-secondary">{item.example}</p>
            </motion.div>
          );
        })}
      </motion.div>
    </LessonSection>
  );
}
