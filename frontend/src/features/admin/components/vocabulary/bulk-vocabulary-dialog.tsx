"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";

import { AdminButton, AdminCheckbox } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  analyzeVocabularyBulk,
  saveVocabularyBulk,
  SessionExpiredError,
} from "@/features/admin/services/vocabulary-service";
import type {
  BulkVocabularySaveItem,
  BulkVocabularySaveResult,
} from "@/features/admin/types/content.types";

import BulkVocabularyPreviewTable, { type EditableRow } from "./bulk-vocabulary-preview-table";

type Phase = "input" | "analyzing" | "preview" | "saving" | "result";

interface Progress {
  processed: number;
  total: number;
}

interface Props {
  lessonId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: () => void;
}

let rowIdCounter = 0;
function nextRowId(): string {
  rowIdCounter += 1;
  return `row-${rowIdCounter}`;
}

export default function BulkVocabularyDialog({ lessonId, open, onOpenChange, onSaved }: Props) {
  const [rawText, setRawText] = useState("");
  const [autoComplete, setAutoComplete] = useState(true);
  const [publishImmediately, setPublishImmediately] = useState(false);

  const [phase, setPhase] = useState<Phase>("input");
  const [progress, setProgress] = useState<Progress | null>(null);
  const [rows, setRows] = useState<EditableRow[]>([]);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [saveResult, setSaveResult] = useState<BulkVocabularySaveResult | null>(null);
  const [controller, setController] = useState<AbortController | null>(null);

  function reset() {
    setRawText("");
    setAutoComplete(true);
    setPublishImmediately(false);
    setPhase("input");
    setProgress(null);
    setRows([]);
    setAnalyzeError(null);
    setSessionExpired(false);
    setSaveResult(null);
    setController(null);
  }

  function handleClose(nextOpen: boolean) {
    if (!nextOpen) reset();
    onOpenChange(nextOpen);
  }

  async function handleAnalyze() {
    const words = rawText.split(/\r?\n/);
    if (words.every((w) => !w.trim())) return;

    setAnalyzeError(null);
    setSessionExpired(false);
    setRows([]);
    setProgress(null);
    setPhase("analyzing");

    const abort = new AbortController();
    setController(abort);

    try {
      for await (const event of analyzeVocabularyBulk(
        { lesson_id: lessonId, words, auto_complete: autoComplete },
        abort.signal,
      )) {
        if (event.type === "progress") {
          setProgress({ processed: event.processed, total: event.total });
        } else if (event.type === "item") {
          setRows((prev) => [
            ...prev,
            {
              rowId: nextRowId(),
              forceDuplicate: false,
              input_word: event.input_word,
              word_type: event.word_type,
              article: event.article,
              german_word: event.german_word,
              plural: event.plural,
              translation: event.translation,
              example_sentence: event.example_sentence,
              example_translation: event.example_translation,
              is_duplicate: event.is_duplicate,
            },
          ]);
        } else if (event.type === "error") {
          setAnalyzeError(event.message);
        }
      }
      setPhase((current) => (current === "analyzing" ? "preview" : current));
    } catch (err) {
      if (!abort.signal.aborted) {
        // Never rendered as the same "Gemini overloaded" text — a
        // distinct message and a reload action, since retrying this
        // dialog alone can't fix an expired session.
        if (err instanceof SessionExpiredError) {
          setSessionExpired(true);
        }
        setAnalyzeError(err instanceof Error ? err.message : "Analyse fehlgeschlagen.");
      }
      setPhase("input");
    } finally {
      setController(null);
    }
  }

  function handleCancelAnalyze() {
    controller?.abort();
    setPhase("input");
  }

  function updateRow(rowId: string, patch: Partial<EditableRow>) {
    setRows((prev) => prev.map((r) => (r.rowId === rowId ? { ...r, ...patch } : r)));
  }

  function removeRow(rowId: string) {
    setRows((prev) => prev.filter((r) => r.rowId !== rowId));
  }

  async function handleSaveAll() {
    setPhase("saving");
    try {
      const items: BulkVocabularySaveItem[] = rows.map((r) => ({
        german_word: r.german_word,
        article: r.article,
        plural: r.plural,
        translation: r.translation,
        example_sentence: r.example_sentence,
        example_translation: r.example_translation,
        is_published: publishImmediately,
        force_duplicate: r.forceDuplicate,
      }));

      const result = await saveVocabularyBulk(lessonId, items);
      setSaveResult(result);
      setPhase("result");
      if (result.saved_count > 0) onSaved();
    } catch {
      setAnalyzeError("Speichern fehlgeschlagen.");
      setPhase("preview");
    }
  }

  const progressPercent = progress && progress.total > 0 ? Math.round((progress.processed / progress.total) * 100) : 0;
  const analyzeDisabled = phase === "analyzing" || rawText.trim().length === 0;

  return (
    <FormDialog
      open={open}
      onOpenChange={handleClose}
      title="Bulk Wortschatz erstellen"
      size="xl"
      footer={
        <>
          <AdminButton variant="ghost" onClick={() => handleClose(false)}>
            {phase === "result" ? "Schließen" : "Abbrechen"}
          </AdminButton>

          {phase === "input" && (
            <AdminButton onClick={handleAnalyze} disabled={analyzeDisabled}>
              <Sparkles size={15} />
              Wörter analysieren
            </AdminButton>
          )}

          {phase === "analyzing" && (
            <AdminButton variant="ghost" onClick={handleCancelAnalyze}>
              Abbrechen
            </AdminButton>
          )}

          {(phase === "preview" || phase === "saving") && (
            <AdminButton onClick={handleSaveAll} disabled={rows.length === 0 || phase === "saving"}>
              {phase === "saving" ? "Wird gespeichert..." : "Alle speichern"}
            </AdminButton>
          )}
        </>
      }
    >
      <div className="space-y-4">
        {phase === "input" && (
          <>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
                Deutsche Wörter hier einfügen...
              </label>
              <textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                rows={10}
                placeholder={"Haus\nWohnung\narbeiten\nbesuchen\nfreundlich"}
                className="w-full resize-y rounded-lg bg-[var(--admin-card)] px-3.5 py-2.5 text-sm text-[var(--admin-text-primary)] outline-none ring-1 ring-[var(--admin-border-strong)] transition placeholder:text-[var(--admin-text-muted)] focus:ring-2 focus:ring-[var(--admin-primary)]"
              />
              <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
                Ein Wort pro Zeile. Nummerierung und Aufzählungszeichen werden automatisch entfernt.
              </p>
            </div>

            <div className="space-y-2.5">
              <label className="flex cursor-pointer items-center gap-2.5">
                <AdminCheckbox checked={autoComplete} onCheckedChange={setAutoComplete} />
                <span className="text-sm text-[var(--admin-text-secondary)]">Automatisch vervollständigen</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2.5">
                <AdminCheckbox checked={publishImmediately} onCheckedChange={setPublishImmediately} />
                <span className="text-sm text-[var(--admin-text-secondary)]">Sofort veröffentlichen</span>
              </label>
            </div>

            <p className="text-xs text-[var(--admin-text-muted)]">
              🎙️ Audio wird nicht automatisch erstellt — nach dem Speichern kann es pro Wort oder
              nacheinander für die ganze Lektion mit dem Mikrofon aufgenommen werden.
            </p>

            {analyzeError && (
              <div className="space-y-2">
                <p className="text-sm text-[var(--admin-danger)]">{analyzeError}</p>
                {sessionExpired && (
                  <AdminButton type="button" variant="secondary" size="sm" onClick={() => window.location.reload()}>
                    Seite neu laden
                  </AdminButton>
                )}
              </div>
            )}
          </>
        )}

        {phase === "analyzing" && (
          <div className="space-y-4 py-6">
            <div>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="text-[var(--admin-text-secondary)]">Wörter werden analysiert...</span>
                {progress && (
                  <span className="font-semibold text-[var(--admin-text-primary)]">
                    {progress.processed} / {progress.total}
                  </span>
                )}
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-[var(--admin-primary)] transition-all duration-200"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {(phase === "preview" || phase === "saving") && (
          <>
            {analyzeError && (
              <div className="space-y-2">
                <p className="text-sm text-[var(--admin-danger)]">{analyzeError}</p>
                {sessionExpired && (
                  <AdminButton type="button" variant="secondary" size="sm" onClick={() => window.location.reload()}>
                    Seite neu laden
                  </AdminButton>
                )}
              </div>
            )}
            <label className="flex cursor-pointer items-center gap-2.5">
              <AdminCheckbox checked={publishImmediately} onCheckedChange={setPublishImmediately} />
              <span className="text-sm text-[var(--admin-text-secondary)]">Sofort veröffentlichen</span>
            </label>
            <BulkVocabularyPreviewTable rows={rows} onChange={updateRow} onRemove={removeRow} />
            {phase === "saving" && (
              <p className="text-sm text-[var(--admin-text-secondary)]">Wird gespeichert...</p>
            )}
          </>
        )}

        {phase === "result" && saveResult && (
          <div className="space-y-3">
            <p className="text-sm font-semibold text-[var(--admin-accent)]">
              {saveResult.saved_count} Wörter gespeichert
            </p>
            {saveResult.needs_review.length > 0 && (
              <div className="rounded-xl bg-[var(--admin-warning)]/10 p-4">
                <p className="text-sm font-semibold text-[var(--admin-warning)]">
                  {saveResult.needs_review.length} Wörter benötigen Überprüfung
                </p>
                <ul className="mt-2 space-y-1 text-xs text-[var(--admin-text-secondary)]">
                  {saveResult.needs_review.map((item, i) => (
                    <li key={i}>
                      <span className="font-medium">{item.word}</span> — {item.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-xs text-[var(--admin-text-muted)]">
              🎙️ Nutze „Audio nacheinander aufnehmen“ in der Vokabelliste, um jetzt Aufnahmen für die
              neuen Wörter zu machen.
            </p>
          </div>
        )}
      </div>
    </FormDialog>
  );
}
