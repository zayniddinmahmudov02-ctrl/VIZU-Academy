"use client";

import { useState } from "react";

import type { PublicTask, PublicTaskQuestion, TaskType } from "@/features/admin/types/assessment.types";

interface Props {
  task: PublicTask;
  answers: Record<string, string>;
  onAnswerChange: (questionId: string, answerData: string) => void;
}

const SINGLE_SELECT: TaskType[] = ["TRUE_FALSE", "MULTIPLE_CHOICE"];
const MULTI_SELECT: TaskType[] = ["MULTIPLE_SELECT", "IMAGE_SELECTION"];
const MATCHING: TaskType[] = [
  "HEADING_MATCHING",
  "ADVERTISEMENT_MATCHING",
  "TEXT_MATCHING",
  "GAP_MATCHING",
  "DRAG_DROP",
  "CATEGORY_SORTING",
];
const TEXT_ANSWER: TaskType[] = ["SHORT_ANSWER"];

export default function TaskRenderer({ task, answers, onAnswerChange }: Props) {
  return (
    <div className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border sm:p-8">
      <h3 className="text-lg font-bold text-text-primary">{task.title}</h3>
      {task.instructions && <p className="mt-1 text-sm text-text-secondary">{task.instructions}</p>}

      {task.task_type === "CLOZE_TEXT" ? (
        <ClozeRenderer task={task} onAnswerChange={onAnswerChange} />
      ) : (
        <>
          {task.content && (
            <div
              className="prose-editor mt-4 text-text-secondary"
              dangerouslySetInnerHTML={{ __html: task.content }}
            />
          )}

          <div className="mt-5 space-y-5">
            {task.questions.map((question) => (
              <QuestionRenderer
                key={question.id}
                taskType={task.task_type}
                question={question}
                value={answers[question.id]}
                onChange={(value) => onAnswerChange(question.id, value)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function QuestionRenderer({
  taskType,
  question,
  value,
  onChange,
}: {
  taskType: TaskType;
  question: PublicTaskQuestion;
  value: string | undefined;
  onChange: (value: string) => void;
}) {
  if (SINGLE_SELECT.includes(taskType)) {
    const selected: string[] = value ? JSON.parse(value) : [];
    return (
      <div>
        <p className="font-medium text-text-primary">{question.prompt}</p>
        <div className="mt-2.5 space-y-2">
          {question.options.map((option) => (
            <label key={option.id} className="flex cursor-pointer items-center gap-2.5 text-sm text-text-secondary">
              <input
                type="radio"
                name={question.id}
                checked={selected[0] === option.id}
                onChange={() => onChange(JSON.stringify([option.id]))}
                className="h-4 w-4 accent-accent-blue"
              />
              {option.option_text}
            </label>
          ))}
        </div>
      </div>
    );
  }

  if (MULTI_SELECT.includes(taskType)) {
    const selected: string[] = value ? JSON.parse(value) : [];
    return (
      <div>
        <p className="font-medium text-text-primary">{question.prompt}</p>
        <div className="mt-2.5 space-y-2">
          {question.options.map((option) => {
            const checked = selected.includes(option.id);
            return (
              <label key={option.id} className="flex cursor-pointer items-center gap-2.5 text-sm text-text-secondary">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() =>
                    onChange(
                      JSON.stringify(
                        checked ? selected.filter((id) => id !== option.id) : [...selected, option.id],
                      ),
                    )
                  }
                  className="h-4 w-4 accent-accent-blue"
                />
                {option.option_text}
              </label>
            );
          })}
        </div>
      </div>
    );
  }

  if (taskType === "SENTENCE_ORDERING") {
    const order: string[] = value ? JSON.parse(value) : [];
    return (
      <div>
        <p className="font-medium text-text-primary">{question.prompt}</p>
        <div className="mt-2.5 space-y-2">
          {question.options.map((option) => (
            <div key={option.id} className="flex items-center gap-2.5 text-sm text-text-secondary">
              <select
                value={order.indexOf(option.id) + 1 || ""}
                onChange={(e) => {
                  const position = Number(e.target.value) - 1;
                  const next = order.filter((id) => id !== option.id);
                  next.splice(position, 0, option.id);
                  onChange(JSON.stringify(next));
                }}
                className="h-8 w-14 rounded-lg bg-surface-card text-center ring-1 ring-surface-border"
              >
                <option value="">–</option>
                {question.options.map((_, i) => (
                  <option key={i} value={i + 1}>
                    {i + 1}
                  </option>
                ))}
              </select>
              {option.option_text}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (MATCHING.includes(taskType)) {
    const pairs: Record<string, string> = value ? JSON.parse(value) : {};
    return (
      <div>
        {question.prompt && <p className="font-medium text-text-primary">{question.prompt}</p>}
        <div className="mt-2.5 space-y-2.5">
          {question.options.map((option) => (
            <div key={option.id} className="flex flex-wrap items-center gap-2.5 text-sm">
              <span className="min-w-[140px] text-text-secondary">{option.option_text}</span>
              <input
                type="text"
                value={pairs[option.id] ?? ""}
                onChange={(e) => onChange(JSON.stringify({ ...pairs, [option.id]: e.target.value }))}
                className="h-9 flex-1 min-w-[160px] rounded-lg bg-surface-card px-3 text-text-primary ring-1 ring-surface-border outline-none focus:ring-2 focus:ring-accent-blue/50"
                placeholder="Antwort"
              />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (TEXT_ANSWER.includes(taskType)) {
    const text: string = value ? JSON.parse(value) : "";
    return (
      <div>
        <p className="font-medium text-text-primary">{question.prompt}</p>
        <input
          type="text"
          value={text}
          onChange={(e) => onChange(JSON.stringify(e.target.value))}
          className="mt-2.5 h-10 w-full rounded-lg bg-surface-card px-3 text-text-primary ring-1 ring-surface-border outline-none focus:ring-2 focus:ring-accent-blue/50"
        />
      </div>
    );
  }

  return null;
}

function ClozeRenderer({
  task,
  onAnswerChange,
}: {
  task: PublicTask;
  onAnswerChange: (questionId: string, answerData: string) => void;
}) {
  const sortedQuestions = [...task.questions].sort((a, b) => a.sort_order - b.sort_order);
  const [values, setValues] = useState<Record<string, string>>({});

  if (!task.content) return null;

  // Split the passage on gap markers ("data-gap-index") and interleave a
  // text input for each — the Nth gap in the content maps to the Nth
  // question by sort_order (see features/admin/lib/gap-extension.ts,
  // which is what wrote these markers in the admin builder).
  const parts = task.content.split(/<span[^>]*data-gap[^>]*>.*?<\/span>/g);

  return (
    <div className="mt-4 leading-8 text-text-secondary">
      {parts.map((part, i) => (
        <span key={i}>
          <span dangerouslySetInnerHTML={{ __html: part }} />
          {i < sortedQuestions.length && (
            <input
              type="text"
              value={values[sortedQuestions[i].id] ?? ""}
              onChange={(e) => {
                const next = { ...values, [sortedQuestions[i].id]: e.target.value };
                setValues(next);
                onAnswerChange(sortedQuestions[i].id, JSON.stringify(e.target.value));
              }}
              className="mx-1 h-8 w-32 rounded-md bg-surface-card px-2 text-center text-text-primary ring-1 ring-accent-blue/40 outline-none focus:ring-2 focus:ring-accent-blue"
            />
          )}
        </span>
      ))}
    </div>
  );
}
