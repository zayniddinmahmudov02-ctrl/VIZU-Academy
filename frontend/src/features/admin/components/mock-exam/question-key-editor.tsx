"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { AdminInput } from "@/components/admin/admin-ui";
import {
  editOptionText,
  editQuestionText,
  getContentQuestions,
  setQuestionKey,
} from "@/features/admin/services/mock-exam-service";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import type { MockQuestion } from "@/features/admin/types/mock-exam.types";

const LETTERS = "ABCDEFGHIJ";

// Questions of one Lesen / Hören Teil: edit texts, mark the correct option (Lösung). Questions themselves are
// created only by the import (multilevel_import); keys are never guessed — a missing key blocks publishing.
export default function QuestionKeyEditor({
  readingContentId,
  listeningContentId,
  modelTestId,
}: {
  readingContentId?: string;
  listeningContentId?: string;
  modelTestId: string;
}) {
  const queryClient = useQueryClient();
  const params = readingContentId ? { reading_content_id: readingContentId } : { listening_content_id: listeningContentId };
  const queryKey = ["mock-exam-questions", params];
  const { data: questions = [], isLoading } = useQuery({ queryKey, queryFn: () => getContentQuestions(params) });
  const [error, setError] = useState<string | null>(null);

  async function run(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      await queryClient.invalidateQueries({ queryKey });
      await queryClient.invalidateQueries({ queryKey: ["mock-exam-model-test-review", modelTestId] });
    } catch (err) {
      setError(apiErrorMessage(err, "Speichern fehlgeschlagen."));
    }
  }

  if (isLoading) return <p className="text-xs text-[var(--admin-text-muted)]">Fragen werden geladen…</p>;
  if (questions.length === 0) return <p className="text-xs text-[var(--admin-text-muted)]">Keine Fragen in diesem Teil.</p>;

  const missing = questions.filter((q) => !q.options.some((o) => o.is_correct)).length;

  return (
    <div className="space-y-3" data-testid="question-key-editor">
      <p className={`text-xs font-semibold ${missing ? "text-[var(--admin-warning,#f59e0b)]" : "text-[var(--admin-accent)]"}`}>
        {questions.length} Fragen · {questions.length - missing} mit Lösung{missing ? ` · ${missing} ohne Lösung` : ""}
      </p>
      {error && <p className="text-xs text-[var(--admin-danger)]">{error}</p>}
      {questions.map((q) => (
        <QuestionRow key={q.id} question={q} run={run} />
      ))}
    </div>
  );
}

function QuestionRow({ question, run }: { question: MockQuestion; run: (a: () => Promise<unknown>) => Promise<void> }) {
  const hasKey = question.options.some((o) => o.is_correct);
  const multiline = question.question_text.length > 80;
  return (
    <div className="rounded-lg p-3 ring-1 ring-[var(--admin-border)]" data-testid="question-row">
      <div className="mb-2 flex items-start gap-2">
        {hasKey ? (
          <CheckCircle2 size={15} className="mt-1 shrink-0 text-[var(--admin-accent)]" aria-label="Lösung gesetzt" />
        ) : (
          <AlertTriangle size={15} className="mt-1 shrink-0 text-[#f59e0b]" aria-label="Lösung fehlt" />
        )}
        {multiline ? (
          <textarea
            defaultValue={question.question_text}
            rows={4}
            onBlur={(e) => e.target.value !== question.question_text && run(() => editQuestionText(question.id, e.target.value))}
            className="min-h-[80px] w-full rounded-md bg-[var(--admin-input,transparent)] p-2 text-sm text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)]"
          />
        ) : (
          <AdminInput
            defaultValue={question.question_text}
            onBlur={(e) => e.target.value !== question.question_text && run(() => editQuestionText(question.id, e.target.value))}
            className="h-8 flex-1 text-sm"
          />
        )}
      </div>
      <div className="grid gap-1.5 sm:grid-cols-2">
        {question.options.map((o, i) => (
          <div key={o.id} className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => run(() => setQuestionKey(question.id, o.is_correct ? [] : [o.id]))}
              aria-pressed={o.is_correct}
              title={o.is_correct ? "Lösung entfernen" : "Als Lösung markieren"}
              data-testid="key-option"
              className={`flex h-7 min-w-7 shrink-0 items-center justify-center rounded-md px-1.5 text-xs font-bold ring-1 transition ${
                o.is_correct
                  ? "bg-[var(--admin-accent)] text-white ring-[var(--admin-accent)]"
                  : "text-[var(--admin-text-muted)] ring-[var(--admin-border-strong)] hover:text-[var(--admin-text-primary)]"
              }`}
            >
              {LETTERS[i] ?? i + 1}
            </button>
            <AdminInput
              defaultValue={o.option_text}
              onBlur={(e) => e.target.value !== o.option_text && run(() => editOptionText(o.id, e.target.value))}
              className="h-7 flex-1 text-xs"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
