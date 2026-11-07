"use client";

import { Check } from "lucide-react";

import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n/use-translation";

import type { PaperQuestion, PaperTeil } from "../../types/multilevel-exam.types";
import TaskText from "../task-text";

const LETTERS = "ABCDEFGHIJ";
// ORDERING / MATCHING items choose a letter from a list printed in the text (parts A–E, headings A–J)
const LETTER_ONLY = new Set(["ORDERING", "MATCHING"]);

interface Props {
  teil: PaperTeil;
  /** exam: answer buttons; preview: read-only with the keys marked (admin). */
  mode: "exam" | "preview";
  answers?: Record<string, string[]>;
  onAnswer?: (question: PaperQuestion, optionIds: string[]) => void;
  disabled?: boolean;
  savingState?: Record<string, "saving" | "saved" | "error">;
  /** Rendered below the prompt of a Schreiben / Sprechen Teil (editor / recorder). */
  children?: React.ReactNode;
}

/** One Teil of a Multilevel exam paper: instructions, text / image / audio, the Schreiben / Sprechen prompt and the
 * questions. Keys exist only in the admin preview payload; the student paper never contains them. */
export default function PaperTeilView({ teil, mode, answers = {}, onAnswer, disabled, savingState = {}, children }: Props) {
  const { t } = useTranslation();
  return (
    <section className="rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-sm)] ring-1 ring-surface-border sm:p-6" data-testid="paper-teil">
      <h2 className="text-lg font-bold text-text-primary">{teil.title}</h2>
      {teil.instructions && <p className="mt-1 whitespace-pre-line text-sm font-medium text-text-secondary">{teil.instructions}</p>}
      {teil.description && <TaskText value={teil.description} className="mt-3 text-sm" />}

      {teil.kind === "listening" &&
        (teil.audio_url ? (
          <audio controls preload="metadata" controlsList="nodownload noplaybackrate" src={teil.audio_url} className="mt-4 w-full">
            <track kind="captions" />
          </audio>
        ) : (
          <p className="mt-4 rounded-xl bg-surface-hover px-4 py-3 text-sm text-text-muted">{t("multilevelExam.audioMissing")}</p>
        ))}

      {teil.image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={teil.image_url} alt="" className="mt-4 max-h-[460px] w-full rounded-xl object-contain" />
      )}
      {teil.text && <TaskText value={teil.text} className="mt-4 text-[15px] leading-relaxed" />}

      {teil.writing_task && (
        <div className="mt-4 space-y-3">
          <TaskText value={teil.writing_task.task_text} />
          {teil.writing_task.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={teil.writing_task.image_url} alt="" className="max-h-[420px] w-full rounded-xl object-contain" />
          )}
          {mode === "preview" && teil.writing_task.evaluation_rubric && (
            <p className="whitespace-pre-line rounded-xl bg-surface-hover p-3 text-xs text-text-muted">{teil.writing_task.evaluation_rubric}</p>
          )}
        </div>
      )}
      {teil.speaking_task && (
        <div className="mt-4 space-y-3">
          <TaskText value={teil.speaking_task.task_text} />
          {teil.speaking_task.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={teil.speaking_task.image_url} alt="" className="max-h-[460px] w-full rounded-xl object-contain" />
          )}
        </div>
      )}
      {children}

      {teil.questions.length > 0 && (
        <ol className="mt-5 space-y-3">
          {teil.questions.map((q) => (
            <QuestionItem
              key={q.id}
              question={q}
              mode={mode}
              selected={answers[q.id] ?? []}
              disabled={disabled}
              state={savingState[q.id]}
              onSelect={(ids) => onAnswer?.(q, ids)}
            />
          ))}
        </ol>
      )}
    </section>
  );
}

function QuestionItem({
  question,
  mode,
  selected,
  disabled,
  state,
  onSelect,
}: {
  question: PaperQuestion;
  mode: "exam" | "preview";
  selected: string[];
  disabled?: boolean;
  state?: "saving" | "saved" | "error";
  onSelect: (ids: string[]) => void;
}) {
  const { t } = useTranslation();
  const letterOnly = LETTER_ONLY.has(question.question_type);
  const multi = question.question_type === "MULTIPLE_CHOICE";
  const toggle = (id: string) => {
    if (mode !== "exam" || disabled) return;
    if (multi) onSelect(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
    else onSelect(selected.includes(id) ? [] : [id]);
  };
  return (
    <li className="rounded-xl bg-surface-hover/50 p-3 ring-1 ring-surface-border sm:p-4" data-testid="exam-question">
      <div className="flex items-start justify-between gap-3">
        <p className="whitespace-pre-line break-words text-sm font-medium text-text-primary">{question.question_text}</p>
        {state && (
          <span className={cn("shrink-0 text-[11px] font-semibold", state === "error" ? "text-danger" : "text-text-muted")}>
            {state === "saving" ? t("multilevelExam.saving") : state === "saved" ? t("multilevelExam.saved") : t("multilevelExam.saveError")}
          </span>
        )}
      </div>
      <div className={cn("mt-2", letterOnly ? "flex flex-wrap gap-1.5" : "space-y-1.5")}>
        {question.options.map((o, i) => {
          const isSelected = selected.includes(o.id);
          const isKey = mode === "preview" && o.is_correct;
          const letter = LETTERS[i] ?? String(i + 1);
          return (
            <button
              key={o.id}
              type="button"
              onClick={() => toggle(o.id)}
              disabled={mode === "exam" && disabled}
              aria-pressed={isSelected}
              data-testid="exam-option"
              className={cn(
                "flex items-center gap-2 rounded-lg text-left text-sm ring-1 transition-colors",
                letterOnly ? "h-9 min-w-9 justify-center px-2 font-bold" : "w-full px-3 py-2",
                isSelected
                  ? "bg-accent-blue text-white ring-accent-blue"
                  : isKey
                    ? "bg-success/15 text-text-primary ring-success"
                    : "bg-surface-card text-text-secondary ring-surface-border hover:bg-surface-hover",
                mode === "preview" && "cursor-default",
              )}
            >
              {letterOnly ? (
                letter
              ) : (
                <>
                  <span className={cn("w-5 shrink-0 font-bold", isSelected ? "text-white" : "text-text-muted")}>{letter}</span>
                  <span className="break-words">{o.option_text}</span>
                </>
              )}
              {isKey && <Check size={14} className="shrink-0 text-success" />}
            </button>
          );
        })}
      </div>
    </li>
  );
}
