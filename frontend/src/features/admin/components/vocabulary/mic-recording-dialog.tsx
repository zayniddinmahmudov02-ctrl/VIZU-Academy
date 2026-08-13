"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, RotateCcw, Square } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  processVocabularyRecording,
  saveVocabularyRecording,
} from "@/features/admin/services/vocabulary-service";

type Phase = "idle" | "requesting" | "recording" | "processing" | "preview" | "saving" | "error";

interface Props {
  vocabularyId: string;
  germanWord: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: (audioUrl: string) => void;
  /** e.g. "3 / 53" — shown next to the word for the sequential
   * "Audio nacheinander aufnehmen" workflow. Omitted for standalone use. */
  progressLabel?: string;
}

function formatTime(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function MicRecordingDialog({
  vocabularyId,
  germanWord,
  open,
  onOpenChange,
  onSaved,
  progressLabel,
}: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewDuration, setPreviewDuration] = useState<number | null>(null);
  const [previewSize, setPreviewSize] = useState<number | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const processedBlobRef = useRef<Blob | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function resetAll() {
    if (timerRef.current) clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    streamRef.current = null;
    recorderRef.current = null;
    chunksRef.current = [];
    processedBlobRef.current = null;
    setPhase("idle");
    setError(null);
    setElapsed(0);
    setPreviewUrl(null);
    setPreviewDuration(null);
    setPreviewSize(null);
  }

  useEffect(() => {
    if (!open) resetAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function startRecording() {
    setError(null);
    setPhase("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => void handleStopped();

      recorder.start();
      setPhase("recording");
      setElapsed(0);
      timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    } catch {
      setError("Mikrofon-Zugriff nicht möglich. Bitte Berechtigung erteilen.");
      setPhase("error");
    }
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    recorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setPhase("processing");
  }

  async function handleStopped() {
    const rawBlob = new Blob(chunksRef.current, { type: recorderRef.current?.mimeType || "audio/webm" });
    try {
      const processed = await processVocabularyRecording(rawBlob);
      processedBlobRef.current = processed;
      const url = URL.createObjectURL(processed);
      setPreviewUrl(url);
      setPreviewSize(processed.size);
      setPhase("preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verarbeitung fehlgeschlagen.");
      setPhase("error");
    }
  }

  async function handleSave() {
    if (!processedBlobRef.current) return;
    setPhase("saving");
    setError(null);
    try {
      const { audio_url } = await saveVocabularyRecording(vocabularyId, processedBlobRef.current);
      // Reset internal recording state but leave open/close to the
      // caller — standalone use closes on save, the sequential
      // "Audio nacheinander aufnehmen" flow instead swaps in the next
      // word while staying open.
      resetAll();
      onSaved(audio_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speichern fehlgeschlagen.");
      setPhase("error");
    }
  }

  function handleReRecord() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    processedBlobRef.current = null;
    setPreviewUrl(null);
    setPreviewDuration(null);
    setPreviewSize(null);
    setError(null);
    setPhase("idle");
  }

  function handleCancel() {
    resetAll();
    onOpenChange(false);
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={(next) => (next ? onOpenChange(true) : handleCancel())}
      title={`Audio aufnehmen — ${germanWord}${progressLabel ? ` (${progressLabel})` : ""}`}
      size="md"
      footer={
        <>
          <AdminButton variant="ghost" onClick={handleCancel}>
            ✕ Abbrechen
          </AdminButton>
          {phase === "preview" && (
            <>
              <AdminButton variant="secondary" onClick={handleReRecord}>
                <RotateCcw size={15} />
                Neu aufnehmen
              </AdminButton>
              <AdminButton onClick={handleSave}>✓ Speichern</AdminButton>
            </>
          )}
        </>
      }
    >
      <div className="space-y-4 py-2">
        <p className="text-sm text-[var(--admin-text-secondary)]">
          Das Wort <span className="font-semibold text-[var(--admin-text-primary)]">„{germanWord}“</span> einmal
          deutlich aussprechen. Die Aufnahme wird automatisch bereinigt und 3x wiederholt.
        </p>

        {phase === "idle" && (
          <div className="flex flex-col items-center gap-3 py-6">
            <AdminButton onClick={startRecording}>
              <Mic size={16} />
              Mikrofon aufnehmen
            </AdminButton>
          </div>
        )}

        {phase === "requesting" && (
          <p className="py-6 text-center text-sm text-[var(--admin-text-secondary)]">
            Mikrofon-Berechtigung wird angefordert...
          </p>
        )}

        {phase === "recording" && (
          <div className="flex flex-col items-center gap-4 py-6">
            <p className="text-sm font-medium text-[var(--admin-danger)]">🔴 Aufnahme läuft...</p>
            <p className="text-2xl font-mono text-[var(--admin-text-primary)]">{formatTime(elapsed)}</p>
            <AdminButton variant="secondary" onClick={stopRecording}>
              <Square size={15} />
              Aufnahme stoppen
            </AdminButton>
          </div>
        )}

        {phase === "processing" && (
          <p className="py-6 text-center text-sm text-[var(--admin-text-secondary)]">
            Aufnahme wird bereinigt und 3x wiederholt...
          </p>
        )}

        {phase === "preview" && previewUrl && (
          <div className="space-y-3 rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
            <p className="text-sm font-medium text-[var(--admin-text-primary)]">🔊 Audio anhören</p>
            <audio
              controls
              src={previewUrl}
              className="w-full"
              onLoadedMetadata={(e) => setPreviewDuration(e.currentTarget.duration)}
            />
            <div className="flex gap-4 text-xs text-[var(--admin-text-muted)]">
              <span>Dauer: {previewDuration ? `${previewDuration.toFixed(1)}s` : "—"}</span>
              <span>Größe: {previewSize !== null ? formatBytes(previewSize) : "—"}</span>
              <span>Format: WAV</span>
            </div>
          </div>
        )}

        {phase === "saving" && (
          <p className="py-6 text-center text-sm text-[var(--admin-text-secondary)]">Wird gespeichert...</p>
        )}

        {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

        {phase === "error" && (
          <div className="flex justify-center">
            <AdminButton variant="secondary" onClick={handleReRecord}>
              <RotateCcw size={15} />
              Erneut versuchen
            </AdminButton>
          </div>
        )}
      </div>
    </FormDialog>
  );
}
