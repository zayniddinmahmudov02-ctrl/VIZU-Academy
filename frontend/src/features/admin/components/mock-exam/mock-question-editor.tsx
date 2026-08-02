"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Copy, GripVertical, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import { useCrudMutations } from "@/features/admin/hooks/use-crud";
import {
  duplicateQuestion,
  mockExamQuestionOptionsApi,
  mockExamQuestionsApi,
} from "@/features/admin/services/mock-exam-service";
import { QUESTION_TYPES, type MockQuestion, type MockQuestionOption, type QuestionType } from "@/features/admin/types/mock-exam.types";
import { useQueryClient } from "@tanstack/react-query";

const TYPE_LABELS: Record<QuestionType, string> = {
  SINGLE_CHOICE: "Single Choice",
  MULTIPLE_CHOICE: "Multiple Choice",
  TRUE_FALSE: "Richtig/Falsch",
  MATCHING: "Zuordnung",
  ORDERING: "Reihenfolge",
  FILL_BLANK: "Lückentext",
  DROPDOWN: "Dropdown",
};

const OPTION_BASED_TYPES: QuestionType[] = [
  "SINGLE_CHOICE",
  "MULTIPLE_CHOICE",
  "TRUE_FALSE",
  "MATCHING",
  "ORDERING",
  "DROPDOWN",
];

interface Props {
  parentKey: "reading_content_id" | "listening_content_id";
  parentId: string;
  questions: MockQuestion[];
  queryKey: string;
}

export default function MockQuestionEditor({ parentKey, parentId, questions, queryKey }: Props) {
  const queryClient = useQueryClient();
  const { create, update, remove } = useCrudMutations(queryKey, mockExamQuestionsApi);
  const [expanded, setExpanded] = useState<string | null>(null);

  const sorted = [...questions].sort((a, b) => a.sort_order - b.sort_order);

  async function handleAdd() {
    const created = await create.mutateAsync({
      [parentKey]: parentId,
      question_type: "SINGLE_CHOICE",
      question_text: "Neue Frage",
      points: 1,
      sort_order: sorted.length + 1,
    });
    setExpanded(created.id);
  }

  async function handleDuplicate(question: MockQuestion) {
    await duplicateQuestion(question.id);
    queryClient.invalidateQueries({ queryKey: [queryKey] });
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
            <span className="shrink-0 rounded-full bg-white/5 px-2 py-0.5 text-[10px] font-semibold uppercase text-[var(--admin-text-muted)]">
              {TYPE_LABELS[question.question_type]}
            </span>
            <AdminInput
              defaultValue={question.question_text}
              onBlur={(e) => {
                if (e.target.value !== question.question_text) {
                  update.mutate({ id: question.id, data: { question_text: e.target.value } });
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
                  update.mutate({ id: question.id, data: { points: value } });
                }
              }}
              className="h-8 w-16 text-center text-sm"
              title="Punkte"
            />
            <button
              onClick={() => handleDuplicate(question)}
              aria-label="Frage duplizieren"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-white/5 hover:text-[var(--admin-primary)]"
            >
              <Copy size={13} />
            </button>
            <button
              onClick={() => remove.mutate(question.id)}
              aria-label="Frage löschen"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
            >
              <Trash2 size={13} />
            </button>
          </div>

          {expanded === question.id && (
            <QuestionDetail
              question={question}
              onUpdateType={(type) => update.mutate({ id: question.id, data: { question_type: type } })}
              onUpdateExplanation={(explanation) => update.mutate({ id: question.id, data: { explanation } })}
              onUpdateCorrectText={(text) =>
                update.mutate({ id: question.id, data: { correct_text_answer: text } })
              }
              queryKey={queryKey}
            />
          )}
        </div>
      ))}

      <AdminButton type="button" variant="secondary" size="sm" onClick={handleAdd} disabled={create.isPending}>
        <Plus size={14} />
        Frage hinzufügen
      </AdminButton>
    </div>
  );
}

function QuestionDetail({
  question,
  onUpdateType,
  onUpdateExplanation,
  onUpdateCorrectText,
  queryKey,
}: {
  question: MockQuestion;
  onUpdateType: (type: QuestionType) => void;
  onUpdateExplanation: (value: string) => void;
  onUpdateCorrectText: (value: string) => void;
  queryKey: string;
}) {
  const isOptionBased = OPTION_BASED_TYPES.includes(question.question_type);

  return (
    <div className="space-y-3 border-t border-[var(--admin-border)] p-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
            Fragetyp
          </label>
          <AdminSelect
            value={question.question_type}
            onChange={(e) => onUpdateType(e.target.value as QuestionType)}
            className="h-8 text-sm"
          >
            {QUESTION_TYPES.map((type) => (
              <option key={type} value={type}>
                {TYPE_LABELS[type]}
              </option>
            ))}
          </AdminSelect>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
          Erklärung (optional, wird dem Schüler nach Abgabe gezeigt)
        </label>
        <AdminTextarea
          defaultValue={question.explanation ?? ""}
          rows={2}
          onBlur={(e) => {
            if (e.target.value !== (question.explanation ?? "")) onUpdateExplanation(e.target.value);
          }}
        />
      </div>

      {question.question_type === "FILL_BLANK" ? (
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
            Korrekte Antwort (Lückentext — Groß-/Kleinschreibung wird ignoriert)
          </label>
          <AdminInput
            defaultValue={question.correct_text_answer ?? ""}
            onBlur={(e) => {
              if (e.target.value !== (question.correct_text_answer ?? "")) onUpdateCorrectText(e.target.value);
            }}
            placeholder="Berlin"
          />
        </div>
      ) : (
        isOptionBased && (
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
              Antwortoptionen{" "}
              <span className="font-normal text-[var(--admin-text-muted)]">
                — richtige Antwort nie an das Frontend der Schüler gesendet
              </span>
            </label>
            <OptionsEditor question={question} queryKey={queryKey} />
          </div>
        )
      )}
    </div>
  );
}

function OptionsEditor({ question, queryKey }: { question: MockQuestion; queryKey: string }) {
  const { create, update, remove } = useCrudMutations(queryKey, mockExamQuestionOptionsApi);
  const options = [...question.options].sort((a, b) => a.sort_order - b.sort_order);
  const type = question.question_type;
  const isMatching = type === "MATCHING";
  const isOrdering = type === "ORDERING";
  const isMultiple = type === "MULTIPLE_CHOICE";

  async function handleAdd() {
    await create.mutateAsync({
      question_id: question.id,
      option_text: isMatching ? "Begriff" : "Neue Option",
      match_value: isMatching ? "Zuordnung" : null,
      is_correct: isOrdering || isMatching,
      sort_order: options.length + 1,
    });
  }

  function toggleCorrect(option: MockQuestionOption) {
    if (isMultiple) {
      update.mutate({ id: option.id, data: { is_correct: !option.is_correct } });
      return;
    }
    // Single-select semantics (SINGLE_CHOICE / TRUE_FALSE / DROPDOWN): only one option may be correct.
    options.forEach((o) => {
      if (o.id === option.id && !o.is_correct) {
        update.mutate({ id: o.id, data: { is_correct: true } });
      } else if (o.id !== option.id && o.is_correct) {
        update.mutate({ id: o.id, data: { is_correct: false } });
      }
    });
  }

  return (
    <div className="space-y-2">
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
                update.mutate({ id: option.id, data: { option_text: e.target.value } });
              }
            }}
            placeholder={isMatching ? "Begriff (links)" : "Option"}
            className="h-8 flex-1 text-sm"
          />

          {isMatching && (
            <AdminInput
              defaultValue={option.match_value ?? ""}
              onBlur={(e) => {
                if (e.target.value !== (option.match_value ?? "")) {
                  update.mutate({ id: option.id, data: { match_value: e.target.value } });
                }
              }}
              placeholder="Zuordnung (rechts)"
              className="h-8 flex-1 text-sm"
            />
          )}

          <button
            onClick={() => remove.mutate(option.id)}
            aria-label="Option löschen"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
          >
            <Trash2 size={13} />
          </button>
        </div>
      ))}

      <AdminButton type="button" variant="ghost" size="sm" onClick={handleAdd} disabled={create.isPending}>
        <Plus size={13} />
        Option hinzufügen
      </AdminButton>
    </div>
  );
}
