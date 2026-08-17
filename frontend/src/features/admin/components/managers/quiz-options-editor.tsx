"use client";

import { useMemo, useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput } from "@/components/admin/admin-ui";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { quizOptionsApi } from "@/features/admin/services/quiz-service";
import type { QuizOption, QuizQuestionType } from "@/features/admin/types/content.types";

export default function QuizOptionsEditor({
  questionId,
  questionType = "MULTIPLE_CHOICE",
}: {
  questionId: string;
  questionType?: QuizQuestionType;
}) {
  const isMatching = questionType === "MATCHING";
  const isOrdering = questionType === "SENTENCE_ORDERING";
  const { data: all, isLoading } = useCrudList("quiz-options", quizOptionsApi);
  const { create, update, remove } = useCrudMutations("quiz-options", quizOptionsApi, [
    ["quiz-questions-with-options"],
  ]);

  const options = useMemo(
    () => (all ?? []).filter((o) => o.question_id === questionId),
    [all, questionId],
  );

  const [newText, setNewText] = useState("");

  async function handleAdd() {
    if (!newText.trim()) return;
    await create.mutateAsync({
      question_id: questionId,
      option_text: newText.trim(),
      is_correct: false,
      order_index: options.length + 1,
    });
    setNewText("");
  }

  return (
    <div className="space-y-2">
      {isLoading && <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {options.map((option: QuizOption) => (
        <div key={option.id} className="flex items-center gap-2 rounded-lg bg-white/[0.02] p-2">
          {!isOrdering && (
            <AdminCheckbox
              checked={option.is_correct}
              onCheckedChange={(checked) =>
                update.mutate({ id: option.id, data: { is_correct: checked } })
              }
              aria-label="Richtige Antwort"
            />
          )}
          <AdminInput
            defaultValue={option.option_text}
            onBlur={(e) => {
              if (e.target.value !== option.option_text) {
                update.mutate({ id: option.id, data: { option_text: e.target.value } });
              }
            }}
            placeholder={isOrdering ? "Satzteil..." : undefined}
            className="h-8 flex-1 text-sm"
          />
          {isMatching && (
            <AdminInput
              defaultValue={option.match_value ?? ""}
              placeholder="Paar-Wert..."
              onBlur={(e) => {
                if (e.target.value !== (option.match_value ?? "")) {
                  update.mutate({ id: option.id, data: { match_value: e.target.value } });
                }
              }}
              className="h-8 w-32 shrink-0 text-sm"
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

      <div className="flex items-center gap-2 pt-1">
        <AdminInput
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          placeholder="Neue Antwortmöglichkeit..."
          className="h-8 flex-1 text-sm"
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
        />
        <AdminButton type="button" variant="secondary" size="sm" onClick={handleAdd}>
          <Plus size={13} />
        </AdminButton>
      </div>
    </div>
  );
}
