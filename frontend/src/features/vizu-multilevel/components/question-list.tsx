"use client";

import { motion } from "framer-motion";

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
  /** Translation key of the "Frage n" / "Test n" label. */
  numberLabelKey?: string;
}

/** The multiple-choice block shared by Lesen and Hören. No correct answer
 * and no CEFR level is ever present in the data this renders. */
export default function VizuMultilevelQuestionList({ questions, answers, onSelect, showQuestionPassage, hideNumbers, numberFromOrder, showLetters, numberLabelKey }: Props) {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      {questions.map((question, qi) => (
        <div key={question.id}>
          {!hideNumbers && (
            <p className="mb-2 text-sm font-semibold text-text-primary">{t(numberLabelKey ?? "vizuMultilevel.question", { number: numberFromOrder ? question.order_index : qi + 1 })}</p>
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
                <motion.button
                  key={option.id}
                  type="button"
                  onClick={() => onSelect(question.id, option.id)}
                  whileTap={{ scale: 0.985 }}
                  aria-pressed={selected}
                  className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium shadow-sm ring-1 transition-colors duration-150 ${
                    selected
                      ? "bg-blue-50 text-slate-900 ring-2 ring-blue-600 dark:bg-blue-500/15 dark:text-white"
                      : "bg-surface-card text-text-primary ring-surface-border hover:bg-blue-50/60 hover:ring-blue-300 dark:hover:bg-blue-500/10"
                  }`}
                >
                  <span
                    aria-hidden="true"
                    className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                      selected ? "border-blue-600 bg-blue-600" : "border-slate-300 dark:border-slate-500"
                    }`}
                  >
                    {selected && (
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        className="h-2 w-2 rounded-full bg-white"
                      />
                    )}
                  </span>
                  <span>
                    {showLetters ? `${String.fromCharCode(65 + oi)}) ` : ""}
                    {option.option_text}
                  </span>
                </motion.button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

export { Passage as VizuMultilevelPassage };
