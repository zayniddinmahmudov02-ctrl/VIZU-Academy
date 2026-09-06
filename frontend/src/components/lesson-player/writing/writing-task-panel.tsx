"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, RotateCcw } from "lucide-react";

import type { LessonWriting } from "@/features/lessons/services/writing-service";
import {
  getMyWritingSubmission,
  submitWriting,
  type WritingOwnSubmission,
} from "@/features/lessons/services/writing-submission-service";
import { ApiError } from "@/lib/api";

const GERMAN_CHARS = ["Ä", "Ö", "Ü", "ß"] as const;

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
  const queryClient = useQueryClient();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { data: existing, isLoading } = useQuery({
    queryKey: ["writing-submission", writing.id],
    queryFn: () => getMyWritingSubmission(writing.id),
  });

  const [text, setText] = useState("");
  const [hydrated, setHydrated] = useState(false);
  const [saving, setSaving] = useState<"draft" | "submit" | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load the existing draft/submission's text exactly once per fetch —
  // after that, the textarea is the source of truth (a refetch caused by
  // an unrelated query invalidation must never clobber what the student
  // is mid-typing).
  useEffect(() => {
    if (!hydrated && existing !== undefined) {
      setText(existing?.answer_text ?? "");
      setHydrated(true);
    }
  }, [existing, hydrated]);

  const words = countWords(text);
  const chars = text.length;
  const belowMin = words < writing.min_words;
  const aboveMax = words > writing.max_words;
  const locked = existing?.status === "GRADED" || existing?.status === "SUBMITTED";
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
    setText(next);
    // Restore focus + cursor right after the inserted character — the
    // DOM value update from setText hasn't committed yet on this tick,
    // so the selection restore runs after React re-renders.
    requestAnimationFrame(() => {
      el.focus();
      const pos = start + char.length;
      el.setSelectionRange(pos, pos);
    });
  }

  async function handleSave(submitFinal: boolean) {
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
        queryClient.invalidateQueries({ queryKey: ["section-gate"] });
      }
    } catch (err) {
      if (err instanceof ApiError && typeof err.data === "object" && err.data && "detail" in err.data) {
        setError(String((err.data as { detail: unknown }).detail));
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
      {locked && (
        <div className="flex items-center gap-2 rounded-xl bg-success/10 px-4 py-3 text-sm font-semibold text-success">
          <CheckCircle2 size={16} />
          Aufgabe abgegeben
        </div>
      )}

      {existing?.status === "GRADED" && (
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
        <div className="flex gap-2">
          {GERMAN_CHARS.map((char) => (
            <button
              key={char}
              type="button"
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
          Wörter: {words} ({writing.min_words}–{writing.max_words})
        </span>
        <span>Zeichen: {chars}</span>
        {canEdit && belowMin && <span className="text-warning">Mindestens {writing.min_words} Wörter erforderlich.</span>}
        {canEdit && aboveMax && <span className="text-danger">Maximal {writing.max_words} Wörter erlaubt.</span>}
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      {canEdit && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleSave(false)}
            disabled={saving !== null}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border transition-colors hover:bg-surface-border disabled:opacity-60"
          >
            {saving === "draft" ? "Wird gespeichert..." : "Entwurf speichern"}
          </button>
          <button
            onClick={() => handleSave(true)}
            disabled={saving !== null}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {saving === "submit" ? "Wird abgegeben..." : "Aufgabe abgeben"}
          </button>
        </div>
      )}
    </div>
  );
}
