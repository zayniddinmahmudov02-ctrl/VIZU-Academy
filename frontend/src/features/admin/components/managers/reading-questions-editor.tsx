"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { readingQuestionsApi } from "@/features/admin/services/reading-service";
import type { ReadingQuestion } from "@/features/admin/types/content.types";

import ReadingOptionsEditor from "./reading-options-editor";

export default function ReadingQuestionsEditor({ readingId }: { readingId: string }) {
  const { data: all, isLoading } = useCrudList("reading-questions", readingQuestionsApi);
  const { create, update, remove } = useCrudMutations("reading-questions", readingQuestionsApi);

  const questions = useMemo(
    () => (all ?? []).filter((q) => q.reading_id === readingId),
    [all, readingId],
  );

  const [expanded, setExpanded] = useState<string | null>(null);
  const [newQuestion, setNewQuestion] = useState("");

  async function handleAdd() {
    if (!newQuestion.trim()) return;
    const created = await create.mutateAsync({
      reading_id: readingId,
      question: newQuestion.trim(),
      order_index: questions.length + 1,
    });
    setNewQuestion("");
    setExpanded(created.id);
  }

  return (
    <div className="space-y-3">
      {isLoading && <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {questions.map((question: ReadingQuestion) => (
        <div key={question.id} className="rounded-lg bg-white/[0.02] ring-1 ring-[var(--admin-border)]">
          <div className="flex items-center gap-2 p-3">
            <button
              onClick={() => setExpanded(expanded === question.id ? null : question.id)}
              className="flex h-6 w-6 shrink-0 items-center justify-center text-[var(--admin-text-muted)]"
            >
              {expanded === question.id ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
            </button>
            <AdminInput
              defaultValue={question.question}
              onBlur={(e) => {
                if (e.target.value !== question.question) {
                  update.mutate({ id: question.id, data: { question: e.target.value } });
                }
              }}
              className="h-8 flex-1 text-sm"
            />
            <button
              onClick={() => remove.mutate(question.id)}
              aria-label="Frage löschen"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
            >
              <Trash2 size={13} />
            </button>
          </div>

          {expanded === question.id && (
            <div className="space-y-3 border-t border-[var(--admin-border)] p-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                  Erklärung (optional)
                </label>
                <AdminTextarea
                  defaultValue={question.explanation ?? ""}
                  rows={2}
                  onBlur={(e) => {
                    if (e.target.value !== (question.explanation ?? "")) {
                      update.mutate({ id: question.id, data: { explanation: e.target.value } });
                    }
                  }}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                  Antwortmöglichkeiten (richtige markieren)
                </label>
                <ReadingOptionsEditor questionId={question.id} />
              </div>
            </div>
          )}
        </div>
      ))}

      <div className="flex items-center gap-2">
        <AdminInput
          value={newQuestion}
          onChange={(e) => setNewQuestion(e.target.value)}
          placeholder="Neue Frage..."
          className="h-9 flex-1 text-sm"
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
        />
        <AdminButton type="button" variant="secondary" size="sm" onClick={handleAdd}>
          <Plus size={14} />
          Frage
        </AdminButton>
      </div>
    </div>
  );
}
