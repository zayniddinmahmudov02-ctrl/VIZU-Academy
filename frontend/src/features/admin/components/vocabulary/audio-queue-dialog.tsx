"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Volume2 } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  generateMissingAudio,
  getAudioQueueStatus,
} from "@/features/admin/services/vocabulary-service";
import type { AudioQueueStatus, TtsQuotaStatus } from "@/features/admin/types/content.types";

type Phase = "loading" | "idle" | "running" | "done";

interface WordResult {
  word: string;
  ok: boolean;
  reason: string | null;
}

interface Props {
  lessonId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function QuotaLine({ quota }: { quota: TtsQuotaStatus }) {
  return (
    <div className="rounded-xl bg-white/[0.02] p-3 text-sm ring-1 ring-[var(--admin-border)]">
      <p className="text-[var(--admin-text-secondary)]">
        Audio quota heute: <span className="font-semibold text-[var(--admin-text-primary)]">{quota.used_today} / {quota.max_per_day}</span> verwendet
      </p>
      {quota.exhausted && (
        <p className="mt-1 text-xs text-[var(--admin-warning)]">
          Tägliches Kontingent aufgebraucht. Nächster Versuch nach Quota-Reset (Google, ca. 24h).
        </p>
      )}
    </div>
  );
}

export default function AudioQueueDialog({ lessonId, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<Phase>("loading");
  const [status, setStatus] = useState<AudioQueueStatus | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [results, setResults] = useState<WordResult[]>([]);
  const [runProgress, setRunProgress] = useState<{ processed: number; total: number } | null>(null);
  const [finalQuota, setFinalQuota] = useState<TtsQuotaStatus | null>(null);
  const [stoppedForQuota, setStoppedForQuota] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    void loadStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, lessonId]);

  async function loadStatus() {
    setPhase("loading");
    setLoadError(null);
    try {
      const data = await getAudioQueueStatus(lessonId);
      setStatus(data);
      setPhase("idle");
    } catch {
      setLoadError("Status konnte nicht geladen werden.");
      setPhase("idle");
    }
  }

  function handleClose(nextOpen: boolean) {
    if (!nextOpen) {
      setPhase("loading");
      setStatus(null);
      setResults([]);
      setRunProgress(null);
      setFinalQuota(null);
      setStoppedForQuota(false);
      setRunError(null);
    }
    onOpenChange(nextOpen);
  }

  async function handleRun() {
    setPhase("running");
    setResults([]);
    setRunError(null);
    setStoppedForQuota(false);

    try {
      for await (const event of generateMissingAudio(lessonId)) {
        if (event.type === "queue_start") {
          setRunProgress({ processed: 0, total: event.total });
        } else if (event.type === "word_result") {
          setResults((prev) => [...prev, { word: event.word, ok: event.ok, reason: event.reason }]);
          setRunProgress({ processed: event.processed, total: event.total });
        } else if (event.type === "done") {
          setFinalQuota(event.quota);
          setStoppedForQuota(event.stopped_for_quota);
        }
      }
      setPhase("done");
      // Word rows now carry fresh audio_url/audio_status — refresh the table.
      queryClient.invalidateQueries({ queryKey: ["vocabularies"] });
    } catch (err) {
      setRunError(err instanceof Error ? err.message : "Generierung fehlgeschlagen.");
      setPhase("done");
    }
  }

  const missingCount = status?.total_missing ?? 0;
  const generatedCount = results.filter((r) => r.ok).length;
  const failedCount = results.filter((r) => !r.ok).length;

  return (
    <FormDialog
      open={open}
      onOpenChange={handleClose}
      title="Fehlende Audios generieren"
      size="lg"
      footer={
        <>
          <AdminButton variant="ghost" onClick={() => handleClose(false)}>
            {phase === "done" ? "Schließen" : "Abbrechen"}
          </AdminButton>
          {(phase === "idle" || phase === "done") && (
            <AdminButton
              onClick={handleRun}
              disabled={missingCount === 0 || (status?.quota.exhausted ?? false)}
            >
              <Volume2 size={15} />
              {phase === "done" ? "Erneut versuchen" : `${missingCount} Wörter generieren`}
            </AdminButton>
          )}
        </>
      }
    >
      <div className="space-y-4">
        {phase === "loading" && (
          <p className="text-sm text-[var(--admin-text-secondary)]">Wird geladen...</p>
        )}

        {loadError && <p className="text-sm text-[var(--admin-danger)]">{loadError}</p>}

        {status && phase !== "loading" && phase !== "running" && (
          <>
            <QuotaLine quota={status.quota} />
            <p className="text-sm text-[var(--admin-text-secondary)]">
              {missingCount === 0
                ? "Alle Vokabeln in dieser Lektion haben bereits Audio."
                : `${missingCount} Wörter ohne Audio gefunden.`}
            </p>
            {missingCount > 0 && (
              <div className="max-h-56 space-y-1 overflow-y-auto rounded-xl bg-white/[0.02] p-3 ring-1 ring-[var(--admin-border)]">
                {status.missing.map((w) => (
                  <p key={w.id} className="text-xs text-[var(--admin-text-secondary)]">
                    {w.german_word}
                    <span className="ml-1.5 text-[var(--admin-text-muted)]">
                      — {w.audio_status === "PENDING" ? "noch nicht versucht" : w.audio_status === "FAILED" ? "fehlgeschlagen" : "kontingentiert"}
                    </span>
                  </p>
                ))}
              </div>
            )}
          </>
        )}

        {phase === "running" && (
          <div className="space-y-4 py-2">
            <div>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="text-[var(--admin-text-secondary)]">Audio wird generiert...</span>
                {runProgress && (
                  <span className="font-semibold text-[var(--admin-text-primary)]">
                    {runProgress.processed} / {runProgress.total}
                  </span>
                )}
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-[var(--admin-primary)] transition-all duration-200"
                  style={{
                    width: runProgress && runProgress.total > 0
                      ? `${Math.round((runProgress.processed / runProgress.total) * 100)}%`
                      : "0%",
                  }}
                />
              </div>
              <p className="mt-1.5 text-xs text-[var(--admin-text-muted)]">
                Generiert: {generatedCount} · Fehlgeschlagen: {failedCount}
              </p>
            </div>

            {results.length > 0 && (
              <div className="max-h-56 space-y-1 overflow-y-auto rounded-xl bg-white/[0.02] p-3 ring-1 ring-[var(--admin-border)]">
                {results.map((r, i) => (
                  <p key={i} className="text-xs">
                    {r.ok ? (
                      <span className="text-[var(--admin-accent)]">✓ {r.word}</span>
                    ) : (
                      <span className="text-[var(--admin-danger)]">
                        ❌ {r.word}
                        {r.reason && <span className="ml-1.5 text-[var(--admin-text-muted)]">— {r.reason}</span>}
                      </span>
                    )}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {phase === "done" && (
          <div className="space-y-3">
            {runError && <p className="text-sm text-[var(--admin-danger)]">{runError}</p>}
            <p className="text-sm font-semibold text-[var(--admin-text-primary)]">
              {generatedCount} generiert · {failedCount} fehlgeschlagen
            </p>
            {stoppedForQuota && (
              <p className="text-sm text-[var(--admin-warning)]">
                Vorgang gestoppt: Tägliches Audio-Kontingent aufgebraucht. Nächster Versuch nach Quota-Reset.
              </p>
            )}
            {finalQuota && <QuotaLine quota={finalQuota} />}
          </div>
        )}
      </div>
    </FormDialog>
  );
}
