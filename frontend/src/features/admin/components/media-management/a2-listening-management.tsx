"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, FileAudio2, LoaderCircle, Play, RefreshCw, Upload } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import { getA2AudioOverview, type A2AudioTask } from "@/features/admin/services/media-management-service";
import {
  apiErrorMessage,
  getListeningAudioBlobUrl,
  uploadListeningAudio,
} from "@/features/admin/services/lesson-skills-admin-service";

const MAX_AUDIO_BYTES = 100 * 1024 * 1024;
const AUDIO_ACCEPT = ".mp3,.m4a,audio/mpeg,audio/mp4,audio/x-m4a";
const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";

function formatBytes(bytes: number | null) {
  if (!bytes) return "—";
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

const STATUS_LABEL: Record<string, string> = {
  ok: "Audio vorhanden",
  external: "Externe Audioquelle",
  missing: "Datei fehlt",
  none: "Nicht hochgeladen",
};

/** One existing Hören task of a real A2 lesson. Replacing the audio keeps the
 * task, its questions and answer keys (the server archives the old file). */
function TaskCard({ task, onChanged }: { task: A2AudioTask; onChanged: () => Promise<void> }) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const ok = task.file_status === "ok";

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  function closePreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
  }

  async function uploadFile(file: File | undefined) {
    if (fileInput.current) fileInput.current.value = "";
    if (!file) return;
    if (!/\.(mp3|m4a)$/i.test(file.name)) {
      setError("Nur MP3 oder M4A ist zulässig.");
      return;
    }
    if (file.size > MAX_AUDIO_BYTES) {
      setError("Die Datei überschreitet die maximale Größe von 100 MB.");
      return;
    }
    setBusy(true);
    setProgress(0);
    setError(null);
    setDone(false);
    try {
      await uploadListeningAudio(task.id, file, null, setProgress);
      closePreview();
      await onChanged();
      setDone(true);
    } catch (cause) {
      setError(apiErrorMessage(cause, "Die Audiodatei konnte nicht hochgeladen werden."));
    } finally {
      setBusy(false);
      setProgress(null);
    }
  }

  async function togglePreview() {
    if (previewUrl) return closePreview();
    setBusy(true);
    setError(null);
    try {
      setPreviewUrl(await getListeningAudioBlobUrl(task.id));
    } catch (cause) {
      setError(apiErrorMessage(cause, "Die Audiodatei konnte nicht geladen werden."));
    } finally {
      setBusy(false);
    }
  }

  const extraTracks = task.audio_slots.filter((slot) => slot.id !== "main");

  return (
    <article className="space-y-3 rounded-xl border border-[var(--admin-border)] p-3 sm:p-4" data-testid="a2-audio-task">
      <input
        ref={fileInput}
        type="file"
        accept={AUDIO_ACCEPT}
        className="hidden"
        aria-label={`Audiodatei für ${task.title} auswählen`}
        onChange={(event) => void uploadFile(event.target.files?.[0])}
      />
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]">
            <FileAudio2 size={16} className="shrink-0 text-[var(--admin-primary)]" />
            <span>Hören-Aufgabe {task.order_index}: {task.title}</span>
          </h4>
          <p className="mt-1 break-all text-xs text-[var(--admin-text-muted)]">
            ID {task.id} · {task.question_count} Fragen
            {task.key_missing ? ` · ${task.key_missing} Antwortschlüssel fehlen` : ""}
            {task.is_published ? " · veröffentlicht" : " · Entwurf"}
          </p>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-warning)]/10 text-[var(--admin-warning)]"}`}>
          {STATUS_LABEL[task.file_status] ?? task.file_status}
        </span>
      </div>

      {task.audio_original_name && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--admin-text-secondary)]">
          <span className="break-all">Datei: {task.audio_original_name}</span>
          <span>Format: {task.audio_format ?? "—"}</span>
          <span>Größe: {formatBytes(task.audio_size_bytes)}</span>
          {task.archived_versions > 0 && <span>{task.archived_versions} frühere Version(en) archiviert</span>}
        </div>
      )}
      {task.format_error && (
        <p role="status" className="text-xs font-medium text-[var(--admin-warning)]">
          Format {task.audio_format} wird nicht unterstützt (erlaubt: MP3, M4A).
        </p>
      )}
      {task.material_key && (
        <p className="text-xs text-[var(--admin-text-muted)]">
          Ältere Zuordnung {task.material_key}{task.unverified_source_hint ? ` („${task.unverified_source_hint}“)` : ""} — nicht anhand des Buches bestätigt.
        </p>
      )}
      {extraTracks.length > 0 && (
        <ul className="space-y-0.5 text-xs text-[var(--admin-text-secondary)]">
          {extraTracks.map((slot) => (
            <li key={slot.id} className="break-all">
              Zusatz-Audio {slot.label ?? ""}: {slot.file_name ?? "—"} · {STATUS_LABEL[slot.file_status] ?? slot.file_status}
            </li>
          ))}
        </ul>
      )}

      {previewUrl && <audio controls preload="none" src={previewUrl} className="w-full" aria-label={`${task.title} anhören`} />}

      <div className="flex flex-wrap items-center gap-2">
        <AdminButton size="sm" variant="secondary" disabled={busy || !ok} onClick={() => void togglePreview()}>
          {busy && progress === null ? <LoaderCircle size={14} className="animate-spin" /> : <Play size={14} />}
          {previewUrl ? "Player schließen" : "Audio anhören"}
        </AdminButton>
        <AdminButton size="sm" disabled={busy} onClick={() => fileInput.current?.click()}>
          {busy && progress !== null ? <LoaderCircle size={14} className="animate-spin" /> : <Upload size={14} />}
          {ok ? "Audio ersetzen" : "Audio hochladen"}
        </AdminButton>
        <span className="text-xs text-[var(--admin-text-muted)]">MP3 oder M4A · max. 100 MB</span>
      </div>
      {progress !== null && (
        <div role="status" className="space-y-1">
          <p className="text-xs text-[var(--admin-text-muted)]">Upload läuft … {progress}%</p>
          <div className="h-1.5 overflow-hidden rounded-full bg-[var(--admin-border)]">
            <div className="h-full bg-[var(--admin-primary)]" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}
      {done && <p role="status" className="text-xs text-[var(--admin-success)]">Gespeichert. Aufgabe, Fragen und Antworten bleiben unverändert.</p>}
      {error && <p role="alert" className="text-sm text-[var(--admin-danger)]">{error}</p>}
    </article>
  );
}

export default function A2ListeningManagement() {
  const queryClient = useQueryClient();
  const overview = useQuery({ queryKey: ["media-mgmt", "a2-listening"], queryFn: getA2AudioOverview });

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["media-mgmt", "a2-listening"] }),
      queryClient.invalidateQueries({ queryKey: ["media-mgmt", "items"] }),
    ]);
  }

  const data = overview.data;
  const lessons = [...(data?.lessons ?? [])].sort((a, b) => a.lesson_number - b.lesson_number);

  return (
    <section className="space-y-5" data-testid="a2-listening-management">
      <div className={card}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[var(--admin-text-primary)]">Niveau A2 · Lektionen · Audio</h2>
            <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">
              Lektionen und Hören-Aufgaben stammen aus dem LMS. Es werden keine Audio-Slots erfunden.
            </p>
          </div>
          <AdminButton variant="secondary" size="sm" disabled={overview.isFetching} onClick={() => void refresh()}>
            {overview.isFetching ? <LoaderCircle size={15} className="animate-spin" /> : <RefreshCw size={15} />}
            Aktualisieren
          </AdminButton>
        </div>

        {overview.isPending ? (
          <p role="status" className="mt-4 text-sm text-[var(--admin-text-muted)]">A2-Daten werden geladen …</p>
        ) : overview.isError ? (
          <p role="alert" className="mt-4 text-sm text-[var(--admin-danger)]">A2-Daten konnten nicht geladen werden. Bitte erneut versuchen.</p>
        ) : data && (
          <>
            <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
              {[
                ["Lektionen (LMS)", data.lesson_count],
                ["Erwartete Audio-Slots", data.expected_audio_slots ?? "unbekannt"],
                ["Hören-Aufgaben", data.task_count],
                ["Audio hochgeladen", data.uploaded_audio_count],
                ["Audio fehlt", data.missing_audio_count],
                ["Formatfehler", data.format_error_count],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl border border-[var(--admin-border)] p-3">
                  <dt className="text-xs text-[var(--admin-text-muted)]">{label}</dt>
                  <dd className="mt-1 text-lg font-bold text-[var(--admin-text-primary)]">{value}</dd>
                </div>
              ))}
            </dl>
            {!data.book_confirmed && (
              <div role="status" className="mt-4 flex items-start gap-2 rounded-xl bg-[var(--admin-warning)]/10 p-3 text-sm text-[var(--admin-warning)]">
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <p>Das A2-Buch liegt dem System nicht vor: Slots und Zuordnungen sind nicht anhand des Buches bestätigt. Angezeigt wird nur, was im LMS und im Speicher tatsächlich existiert.</p>
              </div>
            )}
          </>
        )}
      </div>

      {overview.isSuccess && lessons.map((lesson) => (
        <section key={lesson.lesson_id} className={`${card} space-y-4`} data-testid={`a2-lesson-${lesson.lesson_number}`}>
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[var(--admin-border)] pb-3">
            <h3 className="text-base font-bold text-[var(--admin-text-primary)]">
              Lektion {lesson.lesson_number} · {lesson.lesson_title}
            </h3>
            <span className="text-xs text-[var(--admin-text-muted)]">
              {lesson.task_count} Hören-Aufgabe(n) · {lesson.uploaded_count} mit Audio
            </span>
          </div>
          {lesson.tasks.length === 0 ? (
            <p className="text-sm text-[var(--admin-text-muted)]">Keine Hören-Aufgabe in dieser Lektion.</p>
          ) : (
            lesson.tasks.map((task) => <TaskCard key={task.id} task={task} onChanged={refresh} />)
          )}
        </section>
      ))}
    </section>
  );
}
