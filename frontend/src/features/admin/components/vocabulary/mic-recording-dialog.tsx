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

// Preferred order — the first the browser actually supports wins. Never
// force a format the browser doesn't support: MediaRecorder throws
// synchronously on an unsupported mimeType, which would break recording
// entirely on any browser not on this exact list (e.g. Safari, which
// supports none of these and needs the unset-mimeType fallback below).
const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
];

function pickSupportedMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return undefined;
  return PREFERRED_MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type));
}

// Diagnostics only — never logs audio content, tokens, or PII. Kept in
// place (not stripped after the mic-recording bug hunt) since it's the
// only visibility into what a specific admin's specific browser actually
// did, which is exactly what was missing when this broke silently.
function logDiag(label: string, value: unknown) {
  // eslint-disable-next-line no-console
  console.log(`[MicRecording] ${label}:`, value);
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
  const [previewPlayable, setPreviewPlayable] = useState<boolean | null>(null);
  const [previewSize, setPreviewSize] = useState<number | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const processedBlobRef = useRef<Blob | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function stopStreamTracks() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }

  function resetAll() {
    if (timerRef.current) clearInterval(timerRef.current);
    stopStreamTracks();
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    recorderRef.current = null;
    chunksRef.current = [];
    processedBlobRef.current = null;
    setPhase("idle");
    setError(null);
    setElapsed(0);
    setPreviewUrl(null);
    setPreviewDuration(null);
    setPreviewPlayable(null);
    setPreviewSize(null);
  }

  useEffect(() => {
    if (!open) resetAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      stopStreamTracks();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function startRecording() {
    setError(null);
    setPhase("requesting");

    const recorderSupported = typeof MediaRecorder !== "undefined";
    logDiag("MediaRecorder supported", recorderSupported ? "YES" : "NO");
    if (!recorderSupported) {
      setError("Dieser Browser unterstützt keine Audioaufnahme. Bitte Chrome oder Edge verwenden.");
      setPhase("error");
      return;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      logDiag("getUserMedia", "SUCCESS");
      logDiag("Permission", "granted");
    } catch (err) {
      logDiag("getUserMedia", "FAIL");
      const name = err instanceof DOMException ? err.name : "";
      logDiag("Permission", name === "NotAllowedError" ? "denied" : "unknown-error");
      setError(
        name === "NotAllowedError"
          ? "Bitte Mikrofonzugriff für diese Website erlauben."
          : "Mikrofon-Zugriff nicht möglich. Bitte Berechtigung erteilen.",
      );
      setPhase("error");
      return;
    }

    streamRef.current = stream;

    const mimeType = pickSupportedMimeType();
    logDiag("mimeType", mimeType ?? "(browser default)");

    // No mimeType at all if nothing on the preferred list is supported —
    // forcing an unsupported one throws synchronously and would abort
    // the whole recording before it starts.
    const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
    recorderRef.current = recorder;
    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      logDiag("chunks received", chunksRef.current.length);
      // The recorder has now fully flushed everything it's going to —
      // only now is it safe to release the microphone. Stopping the
      // stream's tracks any earlier (e.g. right after calling
      // recorder.stop()) can cut the recorder off mid-finalization and
      // produce an empty or truncated blob, browser-dependent.
      stopStreamTracks();
      void handleStopped();
    };
    recorder.onerror = () => {
      logDiag("recording started", "NO (recorder error)");
      stopStreamTracks();
      setError("Aufnahmefehler. Bitte erneut versuchen.");
      setPhase("error");
    };

    recorder.start();
    logDiag("recording started", "YES");
    setPhase("recording");
    setElapsed(0);
    timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    // Just ask the recorder to stop — the actual stream cleanup happens
    // in onstop, once the final chunk has genuinely arrived.
    recorderRef.current?.stop();
    setPhase("processing");
  }

  async function handleStopped() {
    const mimeType = recorderRef.current?.mimeType || "audio/webm";
    const rawBlob = new Blob(chunksRef.current, { type: mimeType });
    logDiag("blob size", rawBlob.size);
    logDiag("blob type", rawBlob.type);

    if (rawBlob.size === 0) {
      setError("Keine Audioaufnahme erkannt.");
      setPhase("error");
      return;
    }

    try {
      logDiag("upload request", "SENT");
      const processed = await processVocabularyRecording(rawBlob);
      logDiag("backend response status", "OK");
      processedBlobRef.current = processed;
      const url = URL.createObjectURL(processed);
      setPreviewUrl(url);
      setPreviewSize(processed.size);
      logDiag("preview created", "YES");
      setPhase("preview");
    } catch (err) {
      logDiag("upload request", "FAILED");
      logDiag("backend response status", err instanceof Error ? err.message : "unknown");
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
    setPreviewPlayable(null);
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
              onCanPlay={() => {
                setPreviewPlayable(true);
                logDiag("preview playable", "YES");
              }}
              onError={() => {
                setPreviewPlayable(false);
                logDiag("preview playable", "NO");
              }}
            />
            <div className="flex gap-4 text-xs text-[var(--admin-text-muted)]">
              <span>Dauer: {previewDuration ? `${previewDuration.toFixed(1)}s` : "—"}</span>
              <span>Größe: {previewSize !== null ? formatBytes(previewSize) : "—"}</span>
              <span>Format: WAV</span>
            </div>
            {previewPlayable === false && (
              <p className="text-xs text-[var(--admin-danger)]">
                Vorschau konnte nicht abgespielt werden — bitte erneut aufnehmen.
              </p>
            )}
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
