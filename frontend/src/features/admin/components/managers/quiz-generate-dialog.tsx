"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Wand2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  generateQuiz,
  getQuizGenerationTopics,
  type QuizGenerationResponse,
} from "@/features/admin/services/quiz-generation-service";
import type { QuizType } from "@/features/admin/types/content.types";

interface Props {
  lessonId: string;
  quizId: string;
  /** Only GRAMMAR shows the Gemini prompt field below — the deterministic
   * topic/template picker is the only option for every other quiz type,
   * exactly as before. */
  quizType?: QuizType;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Two generation modes share this one dialog: the original deterministic
 * (no AI/LLM) topic/template engine — Niveau + Thema + Anzahl, unchanged,
 * still the only option once the prompt field below is left empty — and,
 * for GRAMMAR quizzes only, an optional "Anweisungen / Prompt" field that
 * routes generation through Gemini instead (see
 * app/services/quiz_generation/quiz_generation_service.
 * generate_quiz_from_prompt) whenever it's non-empty. Both write directly
 * to the quiz (no separate preview/apply step) and share the same Niveau/
 * Anzahl inputs and the same result panel; the deterministic path is
 * "correctness-guaranteed by construction" so it still auto-publishes a
 * GRAMMAR quiz on success (see quiz_generation_service.generate_quiz's
 * docstring) — the Gemini path cannot make that guarantee, so its
 * questions are always created as drafts for the admin to review and
 * publish via the existing "Veröffentlicht" toggles, same as every other
 * AI-generated content type in this admin (Lesen/Hören/Schreiben/
 * Sprechen's "Mit KI erstellen" + Übernehmen flow). */
export default function QuizGenerateDialog({ lessonId, quizId, quizType, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();

  const { data: topicsResponse, isLoading: topicsLoading } = useQuery({
    queryKey: ["quiz-generation-topics", lessonId],
    queryFn: () => getQuizGenerationTopics(lessonId),
    enabled: open,
  });

  const [topic, setTopic] = useState("");
  const [count, setCount] = useState(20);
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [prompt, setPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QuizGenerationResponse | null>(null);

  const supportsAiPrompt = quizType === "GRAMMAR";
  const usingPrompt = supportsAiPrompt && prompt.trim().length > 0;

  const topics = topicsResponse?.topics ?? [];
  const selectedTopic = topics.find((t) => t.topic === topic);

  useEffect(() => {
    if (!open) return;
    setResult(null);
    setError(null);
    setPrompt("");
  }, [open]);

  useEffect(() => {
    if (!topic && topics.length > 0) {
      setTopic(topics[0].topic);
    }
  }, [topic, topics]);

  useEffect(() => {
    setSelectedTypes(new Set(selectedTopic?.question_types.map((t) => t.template_type) ?? []));
  }, [selectedTopic]);

  function toggleType(templateType: string) {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(templateType)) next.delete(templateType);
      else next.add(templateType);
      return next;
    });
  }

  async function handleGenerate() {
    if (!usingPrompt && !topic) return;
    setGenerating(true);
    setError(null);
    try {
      const response = await generateQuiz(
        usingPrompt
          ? { lesson_id: lessonId, quiz_id: quizId, prompt: prompt.trim(), count }
          : {
              lesson_id: lessonId,
              quiz_id: quizId,
              topic,
              count,
              question_types:
                selectedTopic && selectedTypes.size < selectedTopic.question_types.length
                  ? Array.from(selectedTypes)
                  : null,
            },
      );
      setResult(response);
      queryClient.invalidateQueries({ queryKey: ["quiz-questions"] });
      queryClient.invalidateQueries({ queryKey: ["quiz-questions-with-options"] });
      // Generating a GRAMMAR quiz's questions can also flip the quiz
      // container itself to published (see quiz_generation_service.
      // generate_quiz's auto-publish) — without these two, every other
      // admin view reading cached quiz data (QuizManager's own list,
      // and specifically the Courses -> lesson-list content-status
      // table, which is a *separate* query keyed on
      // ["course-lessons-content-status", moduleId]) keeps showing the
      // pre-generation "not published" state until something unrelated
      // happens to invalidate the same keys. Matches the exact keys
      // QuizManager's own create/update/remove mutations already
      // invalidate for the same reason.
      queryClient.invalidateQueries({ queryKey: ["quizzes"] });
      queryClient.invalidateQueries({ queryKey: ["course-lessons-content-status"] });
    } catch {
      setError("Generierung fehlgeschlagen. Bitte erneut versuchen.");
    } finally {
      setGenerating(false);
    }
  }

  function handleClose() {
    onOpenChange(false);
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Grammatik Quiz erstellen"
      description={
        usingPrompt
          ? "Fragen werden von Gemini AI anhand deiner Anweisungen erstellt — als Entwurf, zur Prüfung vor der Veröffentlichung."
          : supportsAiPrompt
            ? "Fragen werden deterministisch aus vordefinierten Vorlagen erstellt — oder gib unten einen Prompt ein, um stattdessen Gemini AI zu verwenden."
            : "Fragen werden deterministisch aus vordefinierten Vorlagen erstellt — keine KI."
      }
      size="lg"
      footer={
        <>
          <AdminButton variant="ghost" onClick={handleClose}>
            {result ? "Fertig" : "Abbrechen"}
          </AdminButton>
          {!result && (
            <AdminButton onClick={handleGenerate} disabled={(!usingPrompt && !topic) || generating}>
              <Wand2 size={14} />
              {generating ? "Wird erstellt..." : "Automatisch erstellen"}
            </AdminButton>
          )}
        </>
      }
    >
      <div className="space-y-4">
        {topicsLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

        {!topicsLoading && !result && (
          <>
            {supportsAiPrompt && (
              <div>
                <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                  Anweisungen / Prompt (optional)
                </label>
                <AdminTextarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={4}
                  placeholder='z. B. "A1 Alphabet mavzusida o‘zbekcha 20 ta murakkab test tuz. 26 ta asosiy harf, 3 ta Umlaut, unli/undoshlar, W/V/J/Z talaffuzi, sch/sp/st/ph/th/ck/ng va diftonglar bo‘yicha savollar ber."'
                  className="text-sm"
                />
                <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
                  Leer lassen, um stattdessen die Vorlagen unten zu verwenden. Bei Eingabe erstellt Gemini AI genau
                  die angeforderte Anzahl Multiple-Choice-Fragen (je 4 Antworten, genau 1 richtig) — auf Usbekisch
                  oder Deutsch formulierbar, die Fragen selbst werden auf Deutsch erstellt, als Entwurf.
                </p>
              </div>
            )}

            {usingPrompt ? (
              <div className="flex items-center gap-3">
                <div className="w-32">
                  <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Niveau</label>
                  <div className="flex h-9 items-center rounded-lg bg-[var(--admin-card)] px-3 text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border-strong)]">
                    {topicsResponse?.level ?? "?"}
                  </div>
                </div>
                <div className="w-28">
                  <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Anzahl</label>
                  <input
                    type="number"
                    min={1}
                    max={500}
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                    className="h-9 w-full rounded-lg bg-[var(--admin-card)] px-3 text-sm text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] outline-none focus:ring-2 focus:ring-[var(--admin-primary)]"
                  />
                </div>
              </div>
            ) : topics.length === 0 ? (
              <p className="rounded-xl bg-white/[0.02] p-4 text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
                Für das Niveau dieser Lektion ({topicsResponse?.level ?? "?"}) ist noch kein Thema registriert.
                {supportsAiPrompt && " Nutze stattdessen den Prompt oben."}
              </p>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <div className="w-32">
                    <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                      Niveau
                    </label>
                    <div className="flex h-9 items-center rounded-lg bg-[var(--admin-card)] px-3 text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border-strong)]">
                      {topicsResponse?.level}
                    </div>
                  </div>
                  <div className="flex-1">
                    <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                      Thema
                    </label>
                    <AdminSelect value={topic} onChange={(e) => setTopic(e.target.value)} className="h-9 text-sm">
                      {topics.map((t) => (
                        <option key={t.topic} value={t.topic}>
                          {t.label}
                        </option>
                      ))}
                    </AdminSelect>
                  </div>
                  <div className="w-28">
                    <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                      Anzahl
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={500}
                      value={count}
                      onChange={(e) => setCount(Number(e.target.value))}
                      className="h-9 w-full rounded-lg bg-[var(--admin-card)] px-3 text-sm text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] outline-none focus:ring-2 focus:ring-[var(--admin-primary)]"
                    />
                  </div>
                </div>

                {selectedTopic && (
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-[var(--admin-text-secondary)]">
                      Fragetypen
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {selectedTopic.question_types.map((qt) => (
                        <label key={qt.template_type} className="flex cursor-pointer items-center gap-2">
                          <AdminCheckbox
                            checked={selectedTypes.has(qt.template_type)}
                            onCheckedChange={() => toggleType(qt.template_type)}
                          />
                          <span className="text-sm text-[var(--admin-text-secondary)]">{qt.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}

        {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

        {result && (
          <div className="space-y-2 rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
            <p className="text-sm font-semibold text-[var(--admin-accent)]">
              {result.created_count} von {result.requested_count} Fragen erstellt
            </p>
            {result.message && <p className="text-xs text-[var(--admin-text-muted)]">{result.message}</p>}
          </div>
        )}
      </div>
    </FormDialog>
  );
}
