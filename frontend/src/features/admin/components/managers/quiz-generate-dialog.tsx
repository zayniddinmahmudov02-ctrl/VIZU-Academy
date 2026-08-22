"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Wand2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminSelect } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  generateQuiz,
  getQuizGenerationTopics,
  type QuizGenerationResponse,
} from "@/features/admin/services/quiz-generation-service";

interface Props {
  lessonId: string;
  quizId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Deterministic (no AI/LLM) question generator — replaces the previous
 * "Mit KI erstellen" Gemini dialog for Grammatik Quiz. Topics and their
 * question types come entirely from GET .../quiz-generation/topics,
 * which reflects whatever's registered server-side for this lesson's
 * level (see app/services/quiz_generation/registry.py) — currently just
 * "Alphabet" for A1; nothing here is Alphabet-specific. Unlike the old
 * AI flow there's no separate preview/apply step: generation writes
 * directly (still as unpublished drafts, same as every other creation
 * path) since the template engine is correctness-guaranteed by
 * construction — there's no AI output to fact-check before it exists. */
export default function QuizGenerateDialog({ lessonId, quizId, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();

  const { data: topicsResponse, isLoading: topicsLoading } = useQuery({
    queryKey: ["quiz-generation-topics", lessonId],
    queryFn: () => getQuizGenerationTopics(lessonId),
    enabled: open,
  });

  const [topic, setTopic] = useState("");
  const [count, setCount] = useState(20);
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QuizGenerationResponse | null>(null);

  const topics = topicsResponse?.topics ?? [];
  const selectedTopic = topics.find((t) => t.topic === topic);

  useEffect(() => {
    if (!open) return;
    setResult(null);
    setError(null);
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
    if (!topic) return;
    setGenerating(true);
    setError(null);
    try {
      const response = await generateQuiz({
        lesson_id: lessonId,
        quiz_id: quizId,
        topic,
        count,
        question_types: selectedTopic && selectedTypes.size < selectedTopic.question_types.length
          ? Array.from(selectedTypes)
          : null,
      });
      setResult(response);
      queryClient.invalidateQueries({ queryKey: ["quiz-questions"] });
      queryClient.invalidateQueries({ queryKey: ["quiz-questions-with-options"] });
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
      description="Fragen werden deterministisch aus vordefinierten Vorlagen erstellt — keine KI."
      size="lg"
      footer={
        <>
          <AdminButton variant="ghost" onClick={handleClose}>
            {result ? "Fertig" : "Abbrechen"}
          </AdminButton>
          {!result && (
            <AdminButton onClick={handleGenerate} disabled={!topic || generating}>
              <Wand2 size={14} />
              {generating ? "Wird erstellt..." : "Automatisch erstellen"}
            </AdminButton>
          )}
        </>
      }
    >
      <div className="space-y-4">
        {topicsLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

        {!topicsLoading && topics.length === 0 && (
          <p className="rounded-xl bg-white/[0.02] p-4 text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
            Für das Niveau dieser Lektion ({topicsResponse?.level ?? "?"}) ist noch kein Thema registriert.
          </p>
        )}

        {!topicsLoading && topics.length > 0 && !result && (
          <>
            <div className="flex items-center gap-3">
              <div className="w-32">
                <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Niveau</label>
                <div className="flex h-9 items-center rounded-lg bg-[var(--admin-card)] px-3 text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border-strong)]">
                  {topicsResponse?.level}
                </div>
              </div>
              <div className="flex-1">
                <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Thema</label>
                <AdminSelect value={topic} onChange={(e) => setTopic(e.target.value)} className="h-9 text-sm">
                  {topics.map((t) => (
                    <option key={t.topic} value={t.topic}>
                      {t.label}
                    </option>
                  ))}
                </AdminSelect>
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
