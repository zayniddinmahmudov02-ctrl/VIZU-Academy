"use client";

import { useState } from "react";
import { CircleHelp } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { useLessonProgressStore } from "@/store/lesson-progress-store";
import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
}

const QUESTION = "Ich ___ Student.";
const OPTIONS = ["bin", "bist", "seid"];
const CORRECT_ANSWER = "bin";

export default function QuizSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const markSectionComplete = useLessonProgressStore((state) => state.markSectionComplete);

  const [selected, setSelected] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);

  const isCorrect = selected === CORRECT_ANSWER;

  function handleSelect(option: string) {
    setSelected(option);
    setChecked(false);
  }

  function handleCheck() {
    if (!selected) return;
    setChecked(true);
    if (selected === CORRECT_ANSWER) {
      markSectionComplete(lessonId, "quiz");
    }
  }

  return (
    <LessonSection
      title={t("lessons.sectionQuiz")}
      description={t("lessons.quizDescription")}
      icon={CircleHelp}
    >
      <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border">
        <h3 className="text-base font-semibold text-text-primary">{QUESTION}</h3>

        <div className="mt-5 space-y-2.5">
          {OPTIONS.map((option) => {
            const isSelected = selected === option;
            const showCorrect = checked && option === CORRECT_ANSWER;
            const showIncorrect = checked && isSelected && option !== CORRECT_ANSWER;

            return (
              <button
                key={option}
                type="button"
                onClick={() => handleSelect(option)}
                className={`w-full rounded-xl px-4 py-3 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                  showCorrect
                    ? "bg-success/10 text-success ring-success/40"
                    : showIncorrect
                      ? "bg-danger/10 text-danger ring-danger/40"
                      : isSelected
                        ? "bg-accent-blue/10 text-text-primary ring-accent-blue/40"
                        : "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30"
                }`}
              >
                {option}
              </button>
            );
          })}
        </div>

        {checked && (
          <p
            className={`mt-4 text-sm font-semibold ${isCorrect ? "text-success" : "text-danger"}`}
          >
            {isCorrect ? t("lessons.quizCorrect") : t("lessons.quizIncorrect")}
          </p>
        )}

        <button
          type="button"
          onClick={handleCheck}
          disabled={!selected}
          className="mt-5 inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {t("lessons.quizCheckAnswer")}
        </button>
      </div>
    </LessonSection>
  );
}
