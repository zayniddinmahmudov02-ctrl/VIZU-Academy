"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Mic } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import { getAudioQueueStatus } from "@/features/admin/services/vocabulary-service";
import type { MissingAudioWord } from "@/features/admin/types/content.types";

import MicRecordingDialog from "./mic-recording-dialog";

interface Props {
  lessonId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** "Audio nacheinander aufnehmen" — records every word in this lesson
 * still missing audio, one after another: record → process → preview →
 * save, then automatically moves to the next word without the admin
 * having to reopen anything. Swaps MicRecordingDialog's target word
 * in place rather than nesting a second dialog. */
export default function SequentialRecordingDialog({ lessonId, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [queue, setQueue] = useState<MissingAudioWord[]>([]);
  const [totalAtStart, setTotalAtStart] = useState(0);
  const [savedCount, setSavedCount] = useState(0);
  const [recording, setRecording] = useState(false);

  useEffect(() => {
    if (!open) {
      setRecording(false);
      return;
    }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, lessonId]);

  async function load() {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await getAudioQueueStatus(lessonId);
      setQueue(data.missing);
      setTotalAtStart(data.missing.length);
      setSavedCount(0);
    } catch {
      setLoadError("Status konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  function handleWordSaved() {
    setSavedCount((c) => c + 1);
    setQueue((prev) => prev.slice(1));
    queryClient.invalidateQueries({ queryKey: ["vocabularies"] });
  }

  const currentWord = queue[0];

  if (recording && currentWord) {
    return (
      <MicRecordingDialog
        key={currentWord.id}
        vocabularyId={currentWord.id}
        germanWord={currentWord.german_word}
        progressLabel={`${totalAtStart - queue.length + 1} / ${totalAtStart}`}
        open={open}
        onOpenChange={onOpenChange}
        onSaved={handleWordSaved}
      />
    );
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Audio nacheinander aufnehmen"
      size="lg"
      footer={
        <>
          <AdminButton variant="ghost" onClick={() => onOpenChange(false)}>
            Schließen
          </AdminButton>
          {queue.length > 0 && (
            <AdminButton onClick={() => setRecording(true)}>
              <Mic size={15} />
              Aufnahme starten
            </AdminButton>
          )}
        </>
      }
    >
      <div className="space-y-4">
        {loading && <p className="text-sm text-[var(--admin-text-secondary)]">Wird geladen...</p>}
        {loadError && <p className="text-sm text-[var(--admin-danger)]">{loadError}</p>}

        {!loading && !loadError && (
          <>
            {recording === false && savedCount > 0 && queue.length === 0 && (
              <p className="text-sm font-semibold text-[var(--admin-accent)]">
                {savedCount} Wörter aufgenommen — alle erledigt.
              </p>
            )}

            {queue.length === 0 && savedCount === 0 && (
              <p className="text-sm text-[var(--admin-text-secondary)]">
                Alle Vokabeln in dieser Lektion haben bereits Audio.
              </p>
            )}

            {queue.length > 0 && (
              <>
                <p className="text-sm text-[var(--admin-text-secondary)]">
                  {queue.length} Wörter ohne Audio{savedCount > 0 ? ` (${savedCount} bereits aufgenommen)` : ""}.
                  Nach jeder Aufnahme geht es automatisch mit dem nächsten Wort weiter.
                </p>
                <div className="max-h-56 space-y-1 overflow-y-auto rounded-xl bg-white/[0.02] p-3 ring-1 ring-[var(--admin-border)]">
                  {queue.map((w) => (
                    <p key={w.id} className="text-xs text-[var(--admin-text-secondary)]">
                      {w.german_word}
                      <span className="ml-1.5 text-[var(--admin-text-muted)]">
                        — {w.audio_status === "FAILED" ? "fehlgeschlagen" : "fehlt"}
                      </span>
                    </p>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </FormDialog>
  );
}
