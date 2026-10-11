"use client";

import { useState } from "react";
import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  apiErrorMessage,
  saveQuestions,
  type AdminQuestion,
  type AdminQuestionType,
} from "@/features/admin/services/lesson-skills-admin-service";

const TRUE_FALSE_OPTIONS = ["Richtig", "Falsch"];

function blankQuestion(type: AdminQuestionType = "MULTIPLE_CHOICE"): AdminQuestion {
  return {
    question: "",
    question_type: type,
    points: 1,
    explanation: null,
    options:
      type === "TRUE_FALSE"
        ? TRUE_FALSE_OPTIONS.map((text, i) => ({ text, is_correct: i === 0 }))
        : ["", "", ""].map((text, i) => ({ text, is_correct: i === 0 })),
  };
}

/** Client-side check mirroring the backend rules (validate_questions):
 * text set, TRUE_FALSE = 2 options, MULTIPLE_CHOICE = 2–6, exactly one
 * correct option, 1–100 points. The server validates again. */
function problems(questions: AdminQuestion[]): string | null {
  for (const [i, q] of questions.entries()) {
    const n = i + 1;
    if (!q.question.trim()) return `Frage ${n}: Fragetext fehlt.`;
    if (q.options.some((o) => !o.text.trim())) return `Frage ${n}: Eine Antwortoption ist leer.`;
    if (q.question_type === "TRUE_FALSE" && q.options.length !== 2) return `Frage ${n}: Richtig/Falsch braucht genau 2 Optionen.`;
    if (q.question_type === "MULTIPLE_CHOICE" && (q.options.length < 2 || q.options.length > 6)) return `Frage ${n}: 2–6 Optionen erlaubt.`;
    if (q.options.filter((o) => o.is_correct).length !== 1) return `Frage ${n}: Genau eine richtige Antwort markieren.`;
    if (!Number.isInteger(q.points) || q.points < 1 || q.points > 100) return `Frage ${n}: Punkte 1–100.`;
  }
  return null;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  kind: "readings" | "listenings";
  ownerId: string;
  title: string;
  initial: AdminQuestion[];
  onSaved: () => void;
}

/** Questions + answer key of one Lesen text / Hören task. Saved as a whole
 * (PUT …/questions); existing questions keep their ids, so attempts that
 * reference them stay valid. */
export default function QuestionEditorDialog({ open, onOpenChange, kind, ownerId, title, initial, onSaved }: Props) {
  const [questions, setQuestions] = useState<AdminQuestion[]>(() => structuredClone(initial));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const total = questions.reduce((sum, q) => sum + (q.points || 0), 0);

  function patch(index: number, change: Partial<AdminQuestion>) {
    setQuestions((prev) => prev.map((q, i) => (i === index ? { ...q, ...change } : q)));
  }

  function setType(index: number, type: AdminQuestionType) {
    const q = questions[index];
    if (q.question_type === type) return;
    patch(index, { question_type: type, options: blankQuestion(type).options });
  }

  function setOption(qi: number, oi: number, text: string) {
    patch(qi, { options: questions[qi].options.map((o, i) => (i === oi ? { ...o, text } : o)) });
  }

  function setCorrect(qi: number, oi: number) {
    patch(qi, { options: questions[qi].options.map((o, i) => ({ ...o, is_correct: i === oi })) });
  }

  function move(index: number, delta: number) {
    const target = index + delta;
    if (target < 0 || target >= questions.length) return;
    setQuestions((prev) => {
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  async function save() {
    const problem = problems(questions);
    if (problem) {
      setError(problem);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await saveQuestions(
        kind,
        ownerId,
        questions.map((q) => ({ ...q, explanation: q.explanation?.trim() ? q.explanation.trim() : null })),
      );
      onSaved();
      onOpenChange(false);
    } catch (err) {
      setError(apiErrorMessage(err, "Speichern fehlgeschlagen."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={`Fragen: ${title}`}
      description={`${questions.length} Fragen · ${total} Punkte · Bewertung: erreichte Punkte / ${total || "—"} × 100`}
      size="xl"
      footer={
        <>
          <AdminButton variant="ghost" onClick={() => onOpenChange(false)}>
            Abbrechen
          </AdminButton>
          <AdminButton onClick={save} disabled={saving} data-testid="questions-save">
            {saving ? "Wird gespeichert..." : "Fragen speichern"}
          </AdminButton>
        </>
      }
    >
      <div className="space-y-4">
        {error && <p className="text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}

        {questions.length === 0 && (
          <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Fragen. Füge die erste Frage hinzu.</p>
        )}

        {questions.map((q, qi) => (
          <div key={q.id ?? `new-${qi}`} className="space-y-3 rounded-xl bg-white/[0.03] p-4 ring-1 ring-[var(--admin-border)]" data-testid="question-row">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-bold text-[var(--admin-text-primary)]">Frage {qi + 1}</span>
              <div className="w-44">
                <AdminSelect value={q.question_type} onChange={(e) => setType(qi, e.target.value as AdminQuestionType)} aria-label="Fragetyp">
                  <option value="MULTIPLE_CHOICE">Multiple Choice</option>
                  <option value="TRUE_FALSE">Richtig / Falsch</option>
                </AdminSelect>
              </div>
              <label className="flex items-center gap-1.5 text-xs text-[var(--admin-text-secondary)]">
                Punkte
                <AdminInput
                  type="number"
                  min={1}
                  max={100}
                  className="h-9 w-20"
                  value={q.points}
                  onChange={(e) => patch(qi, { points: Number(e.target.value) })}
                />
              </label>
              <div className="ml-auto flex gap-1">
                <AdminButton variant="ghost" size="sm" onClick={() => move(qi, -1)} disabled={qi === 0} aria-label="Nach oben">
                  <ArrowUp size={14} />
                </AdminButton>
                <AdminButton variant="ghost" size="sm" onClick={() => move(qi, 1)} disabled={qi === questions.length - 1} aria-label="Nach unten">
                  <ArrowDown size={14} />
                </AdminButton>
                <AdminButton
                  variant="ghost"
                  size="sm"
                  onClick={() => setQuestions((prev) => prev.filter((_, i) => i !== qi))}
                  aria-label="Frage löschen"
                >
                  <Trash2 size={14} />
                </AdminButton>
              </div>
            </div>

            <AdminTextarea
              rows={2}
              value={q.question}
              onChange={(e) => patch(qi, { question: e.target.value })}
              placeholder="Fragetext (nur Fakten aus dem Text / Audio)"
            />

            <div className="space-y-2">
              {q.options.map((o, oi) => (
                <div key={oi} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name={`correct-${qi}`}
                    checked={o.is_correct}
                    onChange={() => setCorrect(qi, oi)}
                    className="h-4 w-4 accent-[var(--admin-primary)]"
                    aria-label={`Option ${oi + 1} ist richtig`}
                  />
                  {q.question_type === "TRUE_FALSE" ? (
                    <span className="text-sm text-[var(--admin-text-primary)]">{o.text}</span>
                  ) : (
                    <>
                      <span className="w-5 text-xs font-bold text-[var(--admin-text-muted)]">{String.fromCharCode(65 + oi)})</span>
                      <AdminInput value={o.text} onChange={(e) => setOption(qi, oi, e.target.value)} placeholder={`Option ${String.fromCharCode(65 + oi)}`} />
                      {q.options.length > 2 && (
                        <AdminButton
                          variant="ghost"
                          size="sm"
                          onClick={() => patch(qi, { options: q.options.filter((_, i) => i !== oi) })}
                          aria-label="Option entfernen"
                        >
                          <Trash2 size={13} />
                        </AdminButton>
                      )}
                    </>
                  )}
                </div>
              ))}
              {q.question_type === "MULTIPLE_CHOICE" && q.options.length < 6 && (
                <button
                  type="button"
                  onClick={() => patch(qi, { options: [...q.options, { text: "", is_correct: false }] })}
                  className="text-xs font-semibold text-[var(--admin-primary)] hover:underline"
                >
                  + Option
                </button>
              )}
            </div>

            <AdminInput
              value={q.explanation ?? ""}
              onChange={(e) => patch(qi, { explanation: e.target.value })}
              placeholder="Erklärung nach der Abgabe (optional)"
            />
          </div>
        ))}

        <div className="flex flex-wrap gap-2">
          <AdminButton variant="secondary" onClick={() => setQuestions((prev) => [...prev, blankQuestion()])} data-testid="question-add-mc">
            <Plus size={15} /> Multiple Choice
          </AdminButton>
          <AdminButton variant="secondary" onClick={() => setQuestions((prev) => [...prev, blankQuestion("TRUE_FALSE")])}>
            <Plus size={15} /> Richtig / Falsch
          </AdminButton>
        </div>
      </div>
    </FormDialog>
  );
}
