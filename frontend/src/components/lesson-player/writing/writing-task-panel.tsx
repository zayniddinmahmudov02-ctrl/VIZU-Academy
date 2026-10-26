"use client";

import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Clock, RotateCcw } from "lucide-react";

import { wordRange, type LessonWriting } from "@/features/lessons/services/writing-service";
import {
  getMyWritingSubmission,
  retryWritingEvaluation,
  submitWriting,
} from "@/features/lessons/services/writing-submission-service";

import AiEvaluationCard from "../common/ai-evaluation-card";
import { ApiError } from "@/lib/api";
import { useTranslation } from "@/lib/i18n/use-translation";

const GERMAN_CHARS = ["ä", "ö", "ü", "ß", "Ä", "Ö", "Ü"] as const;

function countWords(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

/** The real Schreiben writing panel — a plain textarea (per spec: "Oddiy
 * textarea yetarli bo'lsa, mavjud design system bilan textarea ishlat" —
 * no new rich-text editor library added), the four German-character
 * insert buttons, live word/char count against the task's own
 * min_words/max_words, draft save, and submit. Backed by the real
 * StudentWriting submission (see app/models/student_writing.py) — not a
 * fake/local-only draft. */
export default function WritingTaskPanel({ writing }: { writing: LessonWriting }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const ai = !!writing.ai_evaluation_enabled;
  const { data: existing, isLoading } = useQuery({
    queryKey: ["writing-submission", writing.id],
    queryFn: () => getMyWritingSubmission(writing.id),
    // poll while the AI evaluation runs in the background
    refetchInterval: (query) =>
      ai && ["SUBMITTED", "EVALUATING"].includes(query.state.data?.status ?? "") ? 3000 : false,
  });

  const [text, setText] = useState("");
  const [hydrated, setHydrated] = useState(false);
  const [saving, setSaving] = useState<"draft" | "submit" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [newVersion, setNewVersion] = useState(false);
  const [retrying, setRetrying] = useState(false);

  // Load the existing draft/submission's text exactly once per fetch —
  // after that, the textarea is the source of truth (a refetch caused by
  // an unrelated query invalidation must never clobber what the student
  // is mid-typing).
  if (!hydrated && existing !== undefined) {
    // adjust state during render (no effect): runs once, when the data arrives
    setText(existing?.answer_text ?? "");
    setHydrated(true);
  }

  const words = countWords(text);
  const chars = text.length;
  const belowMin = writing.min_words !== null && words < writing.min_words;
  const aboveMax = writing.max_words !== null && words > writing.max_words;
  const range = wordRange(writing.min_words, writing.max_words);
  const status = existing?.status;
  const attemptsUsed = existing?.attempt_count ?? 0;
  const maxAttempts = writing.max_attempts ?? 1;
  const attemptsLeft = Math.max(0, maxAttempts - attemptsUsed);
  const evaluating = status === "SUBMITTED" || status === "EVALUATING";
  // AI tasks: a result (or a failed run) stays visible until the student
  // starts a new version; while evaluating nothing can be edited.
  const locked = ai
    ? evaluating ||
      ((status === "GRADED" || status === "EVALUATION_FAILED") && !newVersion) ||
      (attemptsLeft === 0 && !!status && status !== "DRAFT")
    : status === "GRADED" || status === "SUBMITTED";
  const canEdit = !locked;

  function insertChar(char: string) {
    const el = textareaRef.current;
    if (!el) {
      setText((prev) => prev + char);
      return;
    }
    const start = el.selectionStart ?? text.length;
    const end = el.selectionEnd ?? text.length;
    const next = text.slice(0, start) + char + text.slice(end);
    // commit synchronously, then put the cursor right after the character —
    // no frame in which a keystroke could land at the old cursor position
    flushSync(() => setText(next));
    el.focus();
    const pos = start + char.length;
    el.setSelectionRange(pos, pos);
  }

  async function retry() {
    setRetrying(true);
    try {
      const result = await retryWritingEvaluation(writing.id);
      queryClient.setQueryData(["writing-submission", writing.id], result);
      await queryClient.invalidateQueries({ queryKey: ["writing-submission", writing.id] });
    } catch {
      setError(t("lessons.loadError"));
    } finally {
      setRetrying(false);
    }
  }

  async function handleSave(submitFinal: boolean) {
    setConfirming(false);
    setError(null);
    if (submitFinal && text.trim().length === 0) {
      setError("Bitte schreibe zuerst eine Antwort.");
      return;
    }
    setSaving(submitFinal ? "submit" : "draft");
    try {
      const result = await submitWriting(writing.id, text, submitFinal);
      queryClient.setQueryData(["writing-submission", writing.id], result);
      if (submitFinal) {
        setNewVersion(false);
        queryClient.invalidateQueries({ queryKey: ["section-gate"] });
        queryClient.invalidateQueries({ queryKey: ["lesson-skill-results", writing.lesson_id] });
      }
    } catch (err) {
      const body = err instanceof ApiError && typeof err.data === "object" && err.data ? (err.data as { detail?: unknown; message?: unknown }) : null;
      const message = body ? String(body.message ?? body.detail ?? "") : "";
      if (message === "MAX_ATTEMPTS_REACHED") {
        setError(t("lessons.maxAttemptsReached"));
      } else if (message) {
        setError(message);
      } else {
        setError("Speichern fehlgeschlagen. Bitte versuche es erneut.");
      }
    } finally {
      setSaving(null);
    }
  }

  if (isLoading) {
    return <p className="mt-4 text-sm text-text-muted">Wird geladen...</p>;
  }

  return (
    <div className="mt-4 space-y-3">
      {writing.helper_words && (
        <div className="rounded-xl bg-surface-hover/60 px-4 py-3 text-sm">
          <span className="font-semibold text-text-primary">{t("lessons.helperWords")}: </span>
          <span className="text-text-secondary">{writing.helper_words}</span>
        </div>
      )}

      {ai && attemptsUsed > 0 && (
        <p className="text-xs font-semibold text-text-muted" data-testid="writing-attempts">
          {t("lessons.attemptOf", { n: attemptsUsed, max: maxAttempts })}
        </p>
      )}

      {ai && status && status !== "DRAFT" && !newVersion && (
        <AiEvaluationCard
          status={status}
          score={existing?.score ?? null}
          aiScore={existing?.ai_score ?? null}
          evaluation={existing?.ai_evaluation ?? null}
          onRetry={retry}
          retrying={retrying}
        />
      )}

      {ai && (status === "GRADED" || status === "EVALUATION_FAILED") && !newVersion && (
        attemptsLeft > 0 ? (
          <button
            type="button"
            onClick={() => setNewVersion(true)}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 text-sm font-semibold text-text-primary ring-1 ring-surface-border"
            data-testid="writing-new-version"
          >
            <RotateCcw size={15} />
            {t("lessons.newVersion")}
          </button>
        ) : (
          <p className="text-xs text-text-muted">{t("lessons.maxAttemptsReached")}</p>
        )
      )}

      {!ai && locked && (
        <div className="flex items-center gap-2 rounded-xl bg-success/10 px-4 py-3 text-sm font-semibold text-success">
          <CheckCircle2 size={16} />
          Aufgabe abgegeben
        </div>
      )}

      {!ai && existing?.status === "SUBMITTED" && (
        <div className="flex items-center gap-2 rounded-xl bg-warning/10 px-4 py-3 text-sm font-semibold text-warning">
          <Clock size={16} />
          {t("lessons.statusPending")}
        </div>
      )}

      {!ai && existing?.status === "GRADED" && (
        <div className="rounded-xl bg-surface-hover p-4 ring-1 ring-surface-border">
          <p className="text-sm font-bold text-text-primary">Bewertet: {existing.score}/100 Punkte</p>
          {existing.feedback && <p className="mt-2 text-sm text-text-secondary">{existing.feedback}</p>}
        </div>
      )}

      {existing?.status === "NEEDS_REVISION" && existing.feedback && (
        <div className="flex items-start gap-2 rounded-xl bg-warning/10 px-4 py-3 text-sm text-warning">
          <RotateCcw size={15} className="mt-0.5 shrink-0" />
          <span>
            <strong>Zur Überarbeitung:</strong> {existing.feedback}
          </span>
        </div>
      )}

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-text-primary">Deine Antwort</label>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={!canEdit}
          rows={8}
          className="w-full rounded-xl bg-surface-card p-4 text-[15px] text-text-primary ring-1 ring-surface-border outline-none placeholder:text-text-muted focus:ring-accent-blue disabled:opacity-70 sm:text-sm"
          placeholder="Schreibe hier deine Antwort..."
        />
      </div>

      {canEdit && (
        <div className="flex flex-wrap gap-2">
          {GERMAN_CHARS.map((char) => (
            <button
              key={char}
              type="button"
              // keep the focus (and the mobile keyboard) in the textarea
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => insertChar(char)}
              aria-label={`${char} einfügen`}
              className="flex h-11 w-11 items-center justify-center rounded-xl bg-surface-hover text-base font-bold text-text-primary ring-1 ring-surface-border transition-colors hover:bg-accent-blue hover:text-white"
            >
              {char}
            </button>
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
        <span className={aboveMax ? "font-semibold text-danger" : ""}>
          Wörter: {words}{range ? ` (${range})` : ""}
        </span>
        <span>Zeichen: {chars}</span>
        {canEdit && belowMin && <span className="text-warning">Mindestens {writing.min_words} Wörter erforderlich.</span>}
        {canEdit && aboveMax && <span className="text-danger">Maximal {writing.max_words} Wörter erlaubt.</span>}
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      {canEdit && (
        <div className="flex flex-wrap gap-2">
          {!newVersion && (
            <button
              onClick={() => handleSave(false)}
              disabled={saving !== null}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border transition-colors hover:bg-surface-border disabled:opacity-60"
            >
              {saving === "draft" ? "Wird gespeichert..." : "Entwurf speichern"}
            </button>
          )}
          <button
            onClick={() => (ai ? setConfirming(true) : handleSave(true))}
            disabled={saving !== null}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            data-testid="writing-submit"
          >
            {saving === "submit" ? "Wird abgegeben..." : "Aufgabe abgeben"}
          </button>
        </div>
      )}

      {canEdit && confirming && (
        <div className="flex flex-col gap-3 rounded-xl bg-accent-blue/5 p-4 ring-1 ring-accent-blue/20 sm:flex-row sm:items-center sm:justify-between" role="alertdialog">
          <p className="text-sm font-medium text-text-primary">{t("lessons.submitConfirm")}</p>
          <div className="flex gap-2">
            <button type="button" onClick={() => setConfirming(false)} className="min-h-11 rounded-xl px-4 text-sm font-semibold text-text-secondary ring-1 ring-surface-border">
              {t("lessons.confirmNo")}
            </button>
            <button type="button" onClick={() => handleSave(true)} className="min-h-11 rounded-xl bg-accent-blue px-4 text-sm font-semibold text-white" data-testid="writing-confirm">
              {t("lessons.confirmYes")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
