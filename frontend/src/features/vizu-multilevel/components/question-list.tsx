"use client";

import { useTranslation } from "@/lib/i18n/use-translation";

import type { VizuMultilevelQuestion } from "../types/vizu-multilevel.types";

function Passage({ text }: { text: string }) {
  return (
    <div className="rounded-2xl bg-surface-hover/60 p-4 text-sm leading-relaxed text-text-secondary ring-1 ring-surface-border sm:p-5">
      {text.split("\n").map((line, i) => (
        <p key={i} className={i > 0 ? "mt-2" : undefined}>
          {line}
        </p>
      ))}
    </div>
  );
}

interface Props {
  questions: VizuMultilevelQuestion[];
  answers: Record<string, string>;
  onSelect: (questionId: string, optionId: string) => void;
  /** Lesen questions may carry their own passage; Hören ones never do. */
  showQuestionPassage?: boolean;
  /** Hide the per-question "Frage n" label (Lesen shows "Test n / 20" itself). */
  hideNumbers?: boolean;
  /** Number the question by its own order (1..20) instead of its list position. */
  numberFromOrder?: boolean;
  /** Prefix the options with A) B) C) D). */
  showLetters?: boolean;
}

/** The multiple-choice block shared by Lesen and Hören. No correct answer
 * and no CEFR level is ever present in the data this renders. */
export default function VizuMultilevelQuestionList({ questions, answers, onSelect, showQuestionPassage, hideNumbers, numberFromOrder, showLetters }: Props) {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      {questions.map((question, qi) => (
        <div key={question.id}>
          {!hideNumbers && (
            <p className="mb-2 text-sm font-semibold text-text-primary">{t("vizuMultilevel.question", { number: numberFromOrder ? question.order_index : qi + 1 })}</p>
          )}

          {showQuestionPassage && question.passage_text && (
            <div className="mb-3">
              <Passage text={question.passage_text} />
            </div>
          )}

          <p className="mb-3 text-sm text-text-primary">{question.prompt}</p>

          <div className="space-y-2">
            {question.options.map((option, oi) => {
              const selected = answers[question.id] === option.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => onSelect(question.id, option.id)}
                  className={`w-full rounded-xl px-4 py-3 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                    selected
                      ? "bg-accent-blue/10 text-text-primary ring-accent-blue/40"
                      : "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30"
                  }`}
                >
                  {showLetters ? `${String.fromCharCode(65 + oi)}) ` : ""}
                  {option.option_text}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

export { Passage as VizuMultilevelPassage };
