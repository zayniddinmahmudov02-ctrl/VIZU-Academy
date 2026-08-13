"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";

import { AdminButton, AdminCheckbox } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  analyzeVocabularyBulk,
  saveVocabularyBulk,
} from "@/features/admin/services/vocabulary-service";
import type {
  BulkVocabularySaveItem,
  BulkVocabularySaveResult,
} from "@/features/admin/types/content.types";

import BulkVocabularyPreviewTable, { type EditableRow } from "./bulk-vocabulary-preview-table";

type Phase = "input" | "analyzing" | "preview" | "saving" | "result";

interface Progress {
  phase: "text" | "audio";
  processed: number;
  total: number;
  generated: number;
  failed: number;
}

interface AudioResult {
  word: string;
  ok: boolean;
  reason?: string;
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
  const [generateAudio, setGenerateAudio] = useState(true);
  const [publishImmediately, setPublishImmediately] = useState(false);

  const [phase, setPhase] = useState<Phase>("input");
  const [progress, setProgress] = useState<Progress | null>(null);
  const [audioResults, setAudioResults] = useState<AudioResult[]>([]);
  const [rows, setRows] = useState<EditableRow[]>([]);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [saveResult, setSaveResult] = useState<BulkVocabularySaveResult | null>(null);
  const [controller, setController] = useState<AbortController | null>(null);

  function reset() {
    setRawText("");
    setAutoComplete(true);
    setGenerateAudio(true);
    setPublishImmediately(false);
    setPhase("input");
    setProgress(null);
    setAudioResults([]);
    setRows([]);
    setAnalyzeError(null);
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
    setRows([]);
    setProgress(null);
    setAudioResults([]);
    setPhase("analyzing");

    const abort = new AbortController();
    setController(abort);

    try {
      for await (const event of analyzeVocabularyBulk(
        { lesson_id: lessonId, words, auto_complete: autoComplete, generate_audio: generateAudio },
        abort.signal,
      )) {
        if (event.type === "progress") {
          setProgress({
            phase: event.phase,
            processed: event.processed,
            total: event.total,
            generated: event.generated ?? 0,
            failed: event.failed ?? 0,
          });
        } else if (event.type === "audio_result") {
          setAudioResults((prev) => [
            ...prev,
            event.ok ? { word: event.word, ok: true } : { word: event.word, ok: false, reason: event.reason },
          ]);
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
              audio_url: event.audio_url,
              is_duplicate: event.is_duplicate,
              error: event.error,
            },
          ]);
        } else if (event.type === "error") {
          setAnalyzeError(event.message);
        }
      }
      setPhase((current) => (current === "analyzing" ? "preview" : current));
    } catch (err) {
      if (!abort.signal.aborted) {
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

  async function handleRetryAudio(rowId: string) {
    const row = rows.find((r) => r.rowId === rowId);
    if (!row) return;

    updateRow(rowId, { error: null });

    try {
      // auto_complete=false — the word/article/plural/translation are
      // already good from the first pass; only a fresh audio attempt is
      // wanted, so text re-generation (and its own Gemini call) is
      // skipped entirely.
      for await (const event of analyzeVocabularyBulk({
        lesson_id: lessonId,
        words: [row.german_word],
        auto_complete: false,
        generate_audio: true,
      })) {
        if (event.type === "item") {
          updateRow(rowId, { audio_url: event.audio_url, error: event.error });
        }
      }
    } catch (err) {
      updateRow(rowId, { error: err instanceof Error ? err.message : "Audio konnte nicht erstellt werden." });
    }
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
        audio_url: r.audio_url,
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

          {phase === "preview" && (
            <AdminButton onClick={handleSaveAll} disabled={rows.length === 0}>
              Alle speichern
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
                <AdminCheckbox checked={generateAudio} onCheckedChange={setGenerateAudio} />
                <span className="text-sm text-[var(--admin-text-secondary)]">Deutsche Audio automatisch erstellen</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2.5">
                <AdminCheckbox checked={publishImmediately} onCheckedChange={setPublishImmediately} />
                <span className="text-sm text-[var(--admin-text-secondary)]">Sofort veröffentlichen</span>
              </label>
            </div>

            {analyzeError && <p className="text-sm text-[var(--admin-danger)]">{analyzeError}</p>}
          </>
        )}

        {phase === "analyzing" && (
          <div className="space-y-4 py-6">
            <div>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="text-[var(--admin-text-secondary)]">
                  {progress?.phase === "audio" ? "Audio" : "Wörter werden analysiert..."}
                </span>
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
              {progress?.phase === "audio" && (
                <p className="mt-1.5 text-xs text-[var(--admin-text-muted)]">
                  Generiert: {progress.generated} · Fehlgeschlagen: {progress.failed}
                </p>
              )}
            </div>

            {audioResults.length > 0 && (
              <div className="max-h-56 space-y-1 overflow-y-auto rounded-xl bg-white/[0.02] p-3 ring-1 ring-[var(--admin-border)]">
                {audioResults.map((r, i) => (
                  <p key={i} className="text-xs">
                    {r.ok ? (
                      <span className="text-[var(--admin-accent)]">✓ {r.word}</span>
                    ) : (
                      <span className="text-[var(--admin-danger)]">
                        ❌ {r.word}
                        <span className="ml-1.5 text-[var(--admin-text-muted)]">— {r.reason}</span>
                      </span>
                    )}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {(phase === "preview" || phase === "saving") && (
          <>
            {analyzeError && <p className="text-sm text-[var(--admin-danger)]">{analyzeError}</p>}
            <label className="flex cursor-pointer items-center gap-2.5">
              <AdminCheckbox checked={publishImmediately} onCheckedChange={setPublishImmediately} />
              <span className="text-sm text-[var(--admin-text-secondary)]">Sofort veröffentlichen</span>
            </label>
            <BulkVocabularyPreviewTable
              rows={rows}
              onChange={updateRow}
              onRemove={removeRow}
              onRetryAudio={handleRetryAudio}
            />
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
          </div>
        )}
      </div>
    </FormDialog>
  );
}
