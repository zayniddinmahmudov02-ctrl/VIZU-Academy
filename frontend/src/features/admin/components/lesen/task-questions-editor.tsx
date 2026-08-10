"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, GripVertical, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput } from "@/components/admin/admin-ui";
import type { TaskOption, TaskQuestion, TaskType } from "../../types/assessment.types";

// One generic editor for every option-based task type — mirrors the
// proven pattern in mock-exam/mock-question-editor.tsx (that component
// already handles SINGLE_CHOICE/MULTIPLE_CHOICE/TRUE_FALSE/MATCHING/
// ORDERING/DROPDOWN via one shared options editor with type-aware
// semantics). Extended here to the new 13-type task engine, minus
// CLOZE_TEXT and SHORT_ANSWER — those have their own dedicated editors
// since they answer with free text, not discrete options.
//
// option_text / match_value / is_correct / sort_order are interpreted per
// task_type, same convention as MockQuestionOption:
// - TRUE_FALSE / MULTIPLE_CHOICE / MULTIPLE_SELECT / IMAGE_SELECTION:
//   option_text is the choice, is_correct marks the right one(s).
// - HEADING_MATCHING / ADVERTISEMENT_MATCHING / TEXT_MATCHING /
//   GAP_MATCHING / DRAG_DROP / CATEGORY_SORTING: option_text is the left
//   item (paragraph/person/text/gap/draggable), match_value is its
//   correct right-side pair (heading/ad/text/category/drop-zone).
// - SENTENCE_ORDERING: option_text is the sentence; sort_order IS the
//   correct sequence.

const MATCH_PAIR_TYPES: TaskType[] = [
  "HEADING_MATCHING",
  "ADVERTISEMENT_MATCHING",
  "TEXT_MATCHING",
  "GAP_MATCHING",
  "DRAG_DROP",
  "CATEGORY_SORTING",
];
const ORDERING_TYPES: TaskType[] = ["SENTENCE_ORDERING"];
const MULTI_SELECT_TYPES: TaskType[] = ["MULTIPLE_SELECT", "IMAGE_SELECTION"];

const LEFT_LABEL: Partial<Record<TaskType, string>> = {
  HEADING_MATCHING: "Absatz",
  ADVERTISEMENT_MATCHING: "Person / Anforderung",
  TEXT_MATCHING: "Text",
  GAP_MATCHING: "Lücke",
  DRAG_DROP: "Element",
  CATEGORY_SORTING: "Element",
};
const RIGHT_LABEL: Partial<Record<TaskType, string>> = {
  HEADING_MATCHING: "Überschrift",
  ADVERTISEMENT_MATCHING: "Anzeige",
  TEXT_MATCHING: "Zuordnung",
  GAP_MATCHING: "Antwort",
  DRAG_DROP: "Ablagezone",
  CATEGORY_SORTING: "Kategorie",
};

interface QuestionMutations {
  create: (data: {
    task_id: string;
    prompt: string;
    points: number;
    sort_order: number;
  }) => Promise<TaskQuestion>;
  update: (args: { id: string; data: Partial<TaskQuestion> }) => void;
  remove: (id: string) => void;
}

interface OptionMutations {
  create: (data: {
    question_id: string;
    option_text: string;
    match_value?: string | null;
    is_correct?: boolean;
    sort_order: number;
  }) => void;
  update: (args: { id: string; data: Partial<TaskOption> }) => void;
  remove: (id: string) => void;
}

interface Props {
  taskId: string;
  taskType: TaskType;
  questions: TaskQuestion[];
  questionMutations: QuestionMutations;
  optionMutations: OptionMutations;
}

export default function TaskQuestionsEditor({ taskId, taskType, questions, questionMutations, optionMutations }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const sorted = [...questions].sort((a, b) => a.sort_order - b.sort_order);
  const isMatching = MATCH_PAIR_TYPES.includes(taskType);
  const isOrdering = ORDERING_TYPES.includes(taskType);
  const isMulti = MULTI_SELECT_TYPES.includes(taskType);

  async function handleAdd() {
    const created = await questionMutations.create({
      task_id: taskId,
      prompt: "",
      points: 1,
      sort_order: sorted.length + 1,
    });
    setExpanded(created.id);
  }

  return (
    <div className="space-y-3">
      {sorted.map((question) => (
        <div key={question.id} className="rounded-lg bg-white/[0.02] ring-1 ring-[var(--admin-border)]">
          <div className="flex items-center gap-2 p-3">
            <button
              onClick={() => setExpanded(expanded === question.id ? null : question.id)}
              className="flex h-6 w-6 shrink-0 items-center justify-center text-[var(--admin-text-muted)]"
            >
              {expanded === question.id ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
            </button>
            <AdminInput
              defaultValue={question.prompt}
              placeholder="Frage / Aussage / Absatz..."
              onBlur={(e) => {
                if (e.target.value !== question.prompt) {
                  questionMutations.update({ id: question.id, data: { prompt: e.target.value } });
                }
              }}
              className="h-8 flex-1 text-sm"
            />
            <AdminInput
              type="number"
              defaultValue={question.points}
              onBlur={(e) => {
                const value = Number(e.target.value);
                if (value !== question.points) {
                  questionMutations.update({ id: question.id, data: { points: value } });
                }
              }}
              className="h-8 w-16 text-center text-sm"
              title="Punkte"
            />
            <button
              onClick={() => questionMutations.remove(question.id)}
              aria-label="Löschen"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
            >
              <Trash2 size={13} />
            </button>
          </div>

          {expanded === question.id && (
            <div className="space-y-3 border-t border-[var(--admin-border)] p-3">
              <OptionsEditor
                question={question}
                taskType={taskType}
                isMatching={isMatching}
                isOrdering={isOrdering}
                isMulti={isMulti}
                mutations={optionMutations}
              />
            </div>
          )}
        </div>
      ))}

      <AdminButton type="button" variant="secondary" size="sm" onClick={handleAdd}>
        <Plus size={14} />
        {taskType === "TRUE_FALSE" ? "Aussage hinzufügen" : "Frage hinzufügen"}
      </AdminButton>
    </div>
  );
}

function OptionsEditor({
  question,
  taskType,
  isMatching,
  isOrdering,
  isMulti,
  mutations,
}: {
  question: TaskQuestion;
  taskType: TaskType;
  isMatching: boolean;
  isOrdering: boolean;
  isMulti: boolean;
  mutations: OptionMutations;
}) {
  const options = [...question.options].sort((a, b) => a.sort_order - b.sort_order);
  const leftLabel = LEFT_LABEL[taskType] ?? "Option";
  const rightLabel = RIGHT_LABEL[taskType] ?? "Zuordnung";

  function handleAdd() {
    mutations.create({
      question_id: question.id,
      option_text: "",
      match_value: isMatching ? "" : null,
      is_correct: isOrdering || isMatching,
      sort_order: options.length + 1,
    });
  }

  function toggleCorrect(option: TaskOption) {
    if (isMulti) {
      mutations.update({ id: option.id, data: { is_correct: !option.is_correct } });
      return;
    }
    // Single-correct semantics (TRUE_FALSE / MULTIPLE_CHOICE): exactly one option may be correct.
    options.forEach((o) => {
      if (o.id === option.id && !o.is_correct) {
        mutations.update({ id: o.id, data: { is_correct: true } });
      } else if (o.id !== option.id && o.is_correct) {
        mutations.update({ id: o.id, data: { is_correct: false } });
      }
    });
  }

  return (
    <div className="space-y-2">
      <label className="block text-xs font-medium text-[var(--admin-text-secondary)]">
        {leftLabel} — richtige Antwort nie an das öffentliche Frontend gesendet
      </label>

      {options.map((option, index) => (
        <div key={option.id} className="flex items-center gap-2">
          <GripVertical size={13} className="shrink-0 text-[var(--admin-text-muted)]" />

          {isOrdering && (
            <span className="w-5 shrink-0 text-center text-xs font-semibold text-[var(--admin-text-muted)]">
              {index + 1}
            </span>
          )}

          {!isOrdering && !isMatching && (
            <button
              type="button"
              onClick={() => toggleCorrect(option)}
              aria-label="Als korrekt markieren"
              className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md ring-1 transition ${
                option.is_correct
                  ? "bg-[var(--admin-accent)] text-white ring-[var(--admin-accent)]"
                  : "bg-transparent text-transparent ring-[var(--admin-border-strong)]"
              }`}
            >
              ✓
            </button>
          )}

          <AdminInput
            defaultValue={option.option_text}
            onBlur={(e) => {
              if (e.target.value !== option.option_text) {
                mutations.update({ id: option.id, data: { option_text: e.target.value } });
              }
            }}
            placeholder={leftLabel}
            className="h-8 flex-1 text-sm"
          />

          {isMatching && (
            <AdminInput
              defaultValue={option.match_value ?? ""}
              onBlur={(e) => {
                if (e.target.value !== (option.match_value ?? "")) {
                  mutations.update({ id: option.id, data: { match_value: e.target.value } });
                }
              }}
              placeholder={rightLabel}
              className="h-8 flex-1 text-sm"
            />
          )}

          <button
            onClick={() => mutations.remove(option.id)}
            aria-label="Löschen"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
          >
            <Trash2 size={13} />
          </button>
        </div>
      ))}

      <AdminButton type="button" variant="ghost" size="sm" onClick={handleAdd}>
        <Plus size={13} />
        {rightLabel === leftLabel ? "Hinzufügen" : `${leftLabel} hinzufügen`}
      </AdminButton>
    </div>
  );
}
