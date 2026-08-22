"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Plus, Trash2, Wand2 } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { quizQuestionsApi } from "@/features/admin/services/quiz-service";
import type { QuizQuestion, QuizQuestionType } from "@/features/admin/types/content.types";

import QuizGenerateDialog from "./quiz-generate-dialog";
import QuizOptionsEditor from "./quiz-options-editor";

const QUESTION_TYPE_LABELS: Record<QuizQuestionType, string> = {
  MULTIPLE_CHOICE: "Multiple Choice",
  TRUE_FALSE: "Richtig/Falsch",
  CLOZE_TEXT: "Lückentext",
  SENTENCE_COMPLETION: "Satz ergänzen",
  SENTENCE_ORDERING: "Satz ordnen",
  ERROR_FINDING: "Fehler finden",
  MATCHING: "Zuordnung",
};

// Types graded via the existing options/is_correct mechanism (with
// MATCHING also carrying a match_value per option).
const OPTION_BASED_TYPES: QuizQuestionType[] = [
  "MULTIPLE_CHOICE",
  "TRUE_FALSE",
  "SENTENCE_ORDERING",
  "ERROR_FINDING",
  "MATCHING",
];

interface Props {
  quizId: string;
  lessonId: string;
  /** Hides the "Neue Frage..." add-bar — off for quiz types the admin
   * never manually authors questions for (e.g. VOCABULARY, auto-synced
   * from published vocabulary — see vocabulary-quiz-manager.tsx). */
  allowManualAdd?: boolean;
  /** Hides the "Automatisch erstellen" button (the deterministic
   * template-based generator — see quiz-generate-dialog.tsx) — off for
   * the same non-manually-authored quiz types. */
  allowAiGenerate?: boolean;
}

export default function QuizQuestionsEditor({ quizId, lessonId, allowManualAdd = true, allowAiGenerate = true }: Props) {
  const { data: all, isLoading } = useCrudList("quiz-questions", quizQuestionsApi);
  const { create, update, remove } = useCrudMutations("quiz-questions", quizQuestionsApi, [
    ["quiz-questions-with-options"],
  ]);

  const questions = useMemo(
    () => (all ?? []).filter((q) => q.quiz_id === quizId),
    [all, quizId],
  );

  const [expanded, setExpanded] = useState<string | null>(null);
  const [newQuestion, setNewQuestion] = useState("");
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);

  async function handleAdd() {
    if (!newQuestion.trim()) return;
    const created = await create.mutateAsync({
      quiz_id: quizId,
      question: newQuestion.trim(),
      order_index: questions.length + 1,
    });
    setNewQuestion("");
    setExpanded(created.id);
  }

  return (
    <div className="space-y-3">
      {allowAiGenerate && (
        <div className="flex justify-end">
          <AdminButton type="button" variant="secondary" size="sm" onClick={() => setGenerateDialogOpen(true)}>
            <Wand2 size={13} />
            Automatisch erstellen
          </AdminButton>
        </div>
      )}

      {allowAiGenerate && (
        <QuizGenerateDialog
          lessonId={lessonId}
          quizId={quizId}
          open={generateDialogOpen}
          onOpenChange={setGenerateDialogOpen}
        />
      )}

      {isLoading && <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {questions.map((question: QuizQuestion) => (
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
            <AdminInput
              type="number"
              defaultValue={question.points}
              title="Punkte"
              onBlur={(e) => {
                const value = Number(e.target.value);
                if (value !== question.points) {
                  update.mutate({ id: question.id, data: { points: value } });
                }
              }}
              className="h-8 w-16 shrink-0 text-sm"
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
                  Fragetyp
                </label>
                <AdminSelect
                  value={question.question_type}
                  onChange={(e) =>
                    update.mutate({
                      id: question.id,
                      data: { question_type: e.target.value as QuizQuestionType },
                    })
                  }
                  className="h-8 text-sm"
                >
                  {Object.entries(QUESTION_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </AdminSelect>
              </div>

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

              {OPTION_BASED_TYPES.includes(question.question_type) ? (
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                    {question.question_type === "MATCHING"
                      ? "Antwortmöglichkeiten (Paar-Wert angeben)"
                      : question.question_type === "SENTENCE_ORDERING"
                        ? "Satzteile (in richtiger Reihenfolge anlegen)"
                        : "Antwortmöglichkeiten (richtige markieren)"}
                  </label>
                  <QuizOptionsEditor questionId={question.id} questionType={question.question_type} />
                </div>
              ) : (
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                    Richtige Antwort (Freitext)
                  </label>
                  <AdminInput
                    defaultValue={question.correct_text_answer ?? ""}
                    onBlur={(e) => {
                      if (e.target.value !== (question.correct_text_answer ?? "")) {
                        update.mutate({ id: question.id, data: { correct_text_answer: e.target.value } });
                      }
                    }}
                    className="h-8 text-sm"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      {allowManualAdd && (
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
      )}
    </div>
  );
}
