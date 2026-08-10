"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Clock3, PenLine } from "lucide-react";

import Button from "@/components/ui/button";
import { resolveMediaUrl } from "@/lib/media";
import {
  getWritingResult,
  getWritingSubmission,
  saveWritingDraft,
  submitWriting,
} from "@/features/admin/services/assessment-service";
import type {
  PublicTask,
  WritingResult,
  WritingSubmission,
} from "@/features/admin/types/assessment.types";

interface Props {
  task: PublicTask;
  attemptId: string;
  locked: boolean;
  allowEdit: boolean;
  allowResubmit: boolean;
}

function countWords(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

/** One Schreiben task's two-pane UI — Aufgabe (left) / Schreiben (right) —
 * per spec. "Schreiben starten" opens the editor; Speichern upserts a
 * DRAFT, Abgeben locks the content in and (per the task's evaluation_mode)
 * triggers AI evaluation server-side. Word-limit/lock enforcement here is
 * client-side UX only — the backend re-validates and is the real gate. */
export default function SchreibenTask({ task, attemptId, locked, allowEdit, allowResubmit }: Props) {
  const [submission, setSubmission] = useState<WritingSubmission | null | undefined>(undefined);
  const [result, setResult] = useState<WritingResult | null>(null);
  const [editing, setEditing] = useState(false);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getWritingSubmission(attemptId, task.id).then((s) => {
      setSubmission(s);
      if (s) setContent(s.content);
    });
  }, [attemptId, task.id]);

  useEffect(() => {
    if (submission && submission.status !== "DRAFT") {
      getWritingResult(attemptId, task.id).then(setResult).catch(() => {});
    }
  }, [attemptId, task.id, submission]);

  const wordCount = countWords(content);
  const charCount = content.length;
  const belowMin = task.min_words != null && wordCount < task.min_words;
  const aboveMax = task.max_words != null && wordCount > task.max_words;

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const s = await saveWritingDraft(attemptId, task.id, content);
      setSubmission(s);
    } catch {
      setError("Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit() {
    if (belowMin || aboveMax) return;
    setSubmitting(true);
    setError(null);
    try {
      await saveWritingDraft(attemptId, task.id, content);
      const s = await submitWriting(attemptId, task.id);
      setSubmission(s);
      setEditing(false);
    } catch {
      setError("Abgeben fehlgeschlagen. Prüfe die Wortanzahl.");
    } finally {
      setSubmitting(false);
    }
  }

  const canEdit = !locked && (submission == null || submission.status === "DRAFT" || (allowEdit && allowResubmit));
  const started = editing || submission?.status === "DRAFT";

  return (
    <div className="grid gap-5 rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border sm:p-8 lg:grid-cols-2">
      {/* LEFT — Aufgabe */}
      <div>
        <h3 className="text-lg font-bold text-text-primary">{task.title}</h3>
        {task.instructions && <p className="mt-1 text-sm text-text-secondary">{task.instructions}</p>}
        {task.content && (
          <div
            className="prose-editor mt-4 text-text-secondary"
            dangerouslySetInnerHTML={{ __html: task.content }}
          />
        )}
        {task.image_url && (
          <img
            src={resolveMediaUrl(task.image_url) ?? undefined}
            alt=""
            className="mt-4 max-h-64 w-full rounded-xl object-cover"
          />
        )}
        <div className="mt-4 flex flex-wrap gap-3 text-xs text-text-muted">
          {(task.min_words != null || task.max_words != null) && (
            <span>
              {task.min_words ?? 0}–{task.max_words ?? "∞"} Wörter
            </span>
          )}
          {task.time_limit_minutes != null && (
            <span className="flex items-center gap-1">
              <Clock3 size={12} /> {task.time_limit_minutes} Min.
            </span>
          )}
          <span>{task.max_points} Punkte</span>
        </div>
      </div>

      {/* RIGHT — Schreiben */}
      <div>
        {result && submission && submission.status !== "DRAFT" ? (
          <WritingResultView result={result} />
        ) : !started ? (
          <div className="flex h-full min-h-[220px] flex-col items-center justify-center gap-3 rounded-xl bg-surface-card p-6 text-center ring-1 ring-surface-border">
            <PenLine className="text-accent-blue" size={28} />
            <Button onClick={() => setEditing(true)} disabled={locked}>
              Schreiben starten
            </Button>
          </div>
        ) : (
          <div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={!canEdit}
              rows={10}
              className="w-full rounded-xl bg-surface-card p-4 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-2 focus:ring-accent-blue/50 disabled:opacity-60"
              placeholder="Schreib deinen Text hier..."
            />
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
              <span className={belowMin || aboveMax ? "font-medium text-danger" : ""}>
                {wordCount} Wörter · {charCount} Zeichen
              </span>
            </div>
            {error && <p className="mt-2 text-xs text-danger">{error}</p>}
            {canEdit && (
              <div className="mt-3 flex gap-2">
                <Button variant="secondary" onClick={handleSave} disabled={saving || submitting}>
                  {saving ? "Wird gespeichert..." : "Speichern"}
                </Button>
                <Button onClick={handleSubmit} disabled={saving || submitting || belowMin || aboveMax}>
                  {submitting ? "Wird abgegeben..." : "Abgeben"}
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function WritingResultView({ result }: { result: WritingResult }) {
  const { submission, evaluations, show_feedback } = result;

  if (submission.status === "PENDING_REVIEW") {
    return (
      <div className="flex h-full min-h-[220px] flex-col items-center justify-center gap-2 rounded-xl bg-surface-card p-6 text-center ring-1 ring-surface-border">
        <Clock3 className="text-text-muted" size={24} />
        <p className="text-sm text-text-secondary">Deine Abgabe wird noch von einem Lehrer bewertet.</p>
      </div>
    );
  }

  const latest = evaluations[evaluations.length - 1];

  return (
    <div className="rounded-xl bg-surface-card p-5 ring-1 ring-surface-border">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="text-success" size={20} />
        <span className="text-lg font-bold text-text-primary">{submission.final_score ?? 0} Punkte</span>
      </div>

      {show_feedback && latest && (
        <div className="mt-4 space-y-3 text-sm">
          {Object.keys(latest.rubric_scores).length > 0 && (
            <div className="space-y-1">
              {Object.entries(latest.rubric_scores).map(([id, score]) => (
                <div key={id} className="flex justify-between text-text-secondary">
                  <span>Kriterium</span>
                  <span>{score} Pkt.</span>
                </div>
              ))}
            </div>
          )}
          {latest.strengths && (
            <p className="text-text-secondary">
              <span className="font-medium text-text-primary">Stärken: </span>
              {latest.strengths}
            </p>
          )}
          {latest.feedback && <p className="whitespace-pre-line text-text-secondary">{latest.feedback}</p>}
          {latest.suggestions.length > 0 && (
            <ul className="list-inside list-disc text-text-secondary">
              {latest.suggestions.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
