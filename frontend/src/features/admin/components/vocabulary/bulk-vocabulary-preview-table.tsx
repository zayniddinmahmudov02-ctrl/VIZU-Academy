"use client";

import { useState } from "react";
import { AlertTriangle, Loader2, Play, RotateCcw, Trash2 } from "lucide-react";

import { AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import type { BulkVocabularyPreviewItem, VocabularyWordType } from "@/features/admin/types/content.types";

export interface EditableRow extends BulkVocabularyPreviewItem {
  rowId: string;
  forceDuplicate: boolean;
}

interface Props {
  rows: EditableRow[];
  onChange: (rowId: string, patch: Partial<EditableRow>) => void;
  onRemove: (rowId: string) => void;
  onRetryAudio: (rowId: string) => Promise<void>;
}

const WORD_TYPE_LABEL: Record<VocabularyWordType, string> = {
  NOMEN: "Nomen",
  VERB: "Verb",
  ADJEKTIV: "Adjektiv",
  ADVERB: "Adverb",
  PRONOMEN: "Pronomen",
  PRAEPOSITION: "Präposition",
  KONJUNKTION: "Konjunktion",
  REDEWENDUNG: "Redewendung",
  OTHER: "Sonstige",
};

function playAudio(url: string) {
  new Audio(url).play().catch(() => {});
}

export default function BulkVocabularyPreviewTable({ rows, onChange, onRemove, onRetryAudio }: Props) {
  const [retrying, setRetrying] = useState<Set<string>>(new Set());

  if (rows.length === 0) return null;

  async function handleRetry(rowId: string) {
    setRetrying((prev) => new Set(prev).add(rowId));
    try {
      await onRetryAudio(rowId);
    } finally {
      setRetrying((prev) => {
        const next = new Set(prev);
        next.delete(rowId);
        return next;
      });
    }
  }

  return (
    <div className="overflow-x-auto rounded-xl ring-1 ring-[var(--admin-border)]">
      <table className="w-full min-w-[900px] text-left text-sm">
        <thead className="bg-white/[0.03] text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
          <tr>
            <th className="px-3 py-2.5">#</th>
            <th className="px-3 py-2.5">Artikel</th>
            <th className="px-3 py-2.5">Wort</th>
            <th className="px-3 py-2.5">Plural</th>
            <th className="px-3 py-2.5">Übersetzung</th>
            <th className="px-3 py-2.5">Beispielsatz</th>
            <th className="px-3 py-2.5">Audio</th>
            <th className="px-3 py-2.5" />
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--admin-border)]">
          {rows.map((row, index) => (
            <tr key={row.rowId} className="align-top">
              <td className="px-3 py-2.5 text-[var(--admin-text-muted)]">{index + 1}</td>
              <td className="px-3 py-2.5">
                {row.word_type === "NOMEN" ? (
                  <AdminSelect
                    className="h-9 w-24"
                    value={row.article ?? ""}
                    onChange={(e) => onChange(row.rowId, { article: e.target.value || null })}
                  >
                    <option value="">—</option>
                    <option value="der">der</option>
                    <option value="die">die</option>
                    <option value="das">das</option>
                  </AdminSelect>
                ) : (
                  <span className="text-xs text-[var(--admin-text-muted)]">—</span>
                )}
              </td>
              <td className="px-3 py-2.5">
                <AdminInput
                  className="h-9 w-36"
                  value={row.german_word}
                  onChange={(e) => onChange(row.rowId, { german_word: e.target.value })}
                />
                <p className="mt-1 text-[11px] text-[var(--admin-text-muted)]">{WORD_TYPE_LABEL[row.word_type]}</p>
                {row.is_duplicate && !row.forceDuplicate && (
                  <div className="mt-1.5 rounded-lg bg-[var(--admin-warning)]/10 p-2">
                    <p className="flex items-center gap-1 text-[11px] font-medium text-[var(--admin-warning)]">
                      <AlertTriangle size={11} />
                      Dieses Wort existiert bereits.
                    </p>
                    <div className="mt-1.5 flex gap-1.5">
                      <button
                        type="button"
                        onClick={() => onRemove(row.rowId)}
                        className="rounded-md bg-white/5 px-2 py-1 text-[11px] font-semibold text-[var(--admin-text-secondary)] hover:bg-white/10"
                      >
                        Überspringen
                      </button>
                      <button
                        type="button"
                        onClick={() => onChange(row.rowId, { forceDuplicate: true })}
                        className="rounded-md bg-[var(--admin-primary)]/15 px-2 py-1 text-[11px] font-semibold text-[var(--admin-primary)] hover:bg-[var(--admin-primary)]/25"
                      >
                        Als neues Wort erstellen
                      </button>
                    </div>
                  </div>
                )}
              </td>
              <td className="px-3 py-2.5">
                <AdminInput
                  className="h-9 w-28"
                  value={row.plural ?? ""}
                  placeholder="—"
                  disabled={row.word_type !== "NOMEN"}
                  onChange={(e) => onChange(row.rowId, { plural: e.target.value })}
                />
              </td>
              <td className="px-3 py-2.5">
                <AdminInput
                  className="h-9 w-36"
                  value={row.translation}
                  onChange={(e) => onChange(row.rowId, { translation: e.target.value })}
                />
              </td>
              <td className="px-3 py-2.5">
                <AdminInput
                  className="h-9 w-56"
                  value={row.example_sentence}
                  onChange={(e) => onChange(row.rowId, { example_sentence: e.target.value })}
                />
                <AdminInput
                  className="mt-1.5 h-9 w-56 text-xs"
                  value={row.example_translation}
                  onChange={(e) => onChange(row.rowId, { example_translation: e.target.value })}
                  placeholder="Übersetzung des Beispielsatzes"
                />
              </td>
              <td className="px-3 py-2.5">
                {row.audio_url ? (
                  <button
                    type="button"
                    onClick={() => playAudio(row.audio_url!)}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--admin-primary)]/15 text-[var(--admin-primary)] hover:bg-[var(--admin-primary)]/25"
                    aria-label="Audio abspielen"
                  >
                    <Play size={13} />
                  </button>
                ) : row.error ? (
                  <div className="max-w-[150px]">
                    <p className="text-[11px] text-[var(--admin-danger)]">Audio konnte nicht erstellt werden.</p>
                    <button
                      type="button"
                      onClick={() => handleRetry(row.rowId)}
                      disabled={retrying.has(row.rowId)}
                      className="mt-1 flex items-center gap-1 rounded-md bg-white/5 px-2 py-1 text-[11px] font-semibold text-[var(--admin-text-secondary)] hover:bg-white/10 disabled:opacity-50"
                    >
                      {retrying.has(row.rowId) ? (
                        <Loader2 size={11} className="animate-spin" />
                      ) : (
                        <RotateCcw size={11} />
                      )}
                      Erneut versuchen
                    </button>
                  </div>
                ) : (
                  <span className="text-xs text-[var(--admin-text-muted)]">—</span>
                )}
              </td>
              <td className="px-3 py-2.5">
                <button
                  type="button"
                  onClick={() => onRemove(row.rowId)}
                  aria-label="Zeile entfernen"
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
                >
                  <Trash2 size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
