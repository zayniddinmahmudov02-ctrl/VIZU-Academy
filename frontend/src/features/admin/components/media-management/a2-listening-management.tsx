"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Check, FileAudio2, Link2, LoaderCircle, Play, RefreshCw, Upload } from "lucide-react";

import { AdminButton, AdminSelect } from "@/components/admin/admin-ui";
import {
  assignA2ListeningSlotTask,
  createA2ListeningSlotTask,
  getA2ListeningOverview,
  type A2ListeningMaterial,
  type MediaItem,
} from "@/features/admin/services/media-management-service";
import {
  apiErrorMessage,
  getListeningAudioBlobUrl,
  uploadListeningAudio,
} from "@/features/admin/services/lesson-skills-admin-service";

const MAX_AUDIO_BYTES = 100 * 1024 * 1024;
const AUDIO_ACCEPT = ".mp3,.m4a,audio/mpeg,audio/mp4,audio/x-m4a";
const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";

interface Props {
  mediaItems: MediaItem[];
}

function formatBytes(bytes: number | null) {
  if (!bytes) return "—";
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function SlotCard({
  lessonNumber,
  material,
  lessonTasks,
  onChanged,
}: {
  lessonNumber: number;
  material: A2ListeningMaterial;
  lessonTasks: MediaItem[];
  onChanged: () => Promise<void>;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [selectedTask, setSelectedTask] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const task = material.listening;
  const status = task?.file_status ?? "none";
  const availableTasks = lessonTasks.filter((item) => material.available_task_ids.includes(item.id));

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  async function attachTask() {
    if (!selectedTask) return;
    setBusy(true);
    setError(null);
    try {
      await assignA2ListeningSlotTask(material.key, selectedTask);
      setSelectedTask("");
      await onChanged();
    } catch (cause) {
      setError(apiErrorMessage(cause, "Die vorhandene Aufgabe konnte nicht zugeordnet werden."));
    } finally {
      setBusy(false);
    }
  }

  async function createTask() {
    setBusy(true);
    setError(null);
    try {
      await createA2ListeningSlotTask(lessonNumber, material.key);
      await onChanged();
    } catch (cause) {
      setError(apiErrorMessage(cause, "Die leere Hören-Aufgabe konnte nicht angelegt werden."));
    } finally {
      setBusy(false);
    }
  }

  async function uploadFile(file: File | undefined) {
    if (fileInput.current) fileInput.current.value = "";
    if (!file || !task) return;
    const expectedExtension = material.expected_format.toLowerCase();
    if (file.name.split(".").pop()?.toLowerCase() !== expectedExtension) {
      setError(`Für dieses Material ist nur ${material.expected_format} zulässig.`);
      return;
    }
    if (file.size > MAX_AUDIO_BYTES) {
      setError("Die Datei überschreitet die maximale Größe von 100 MB.");
      return;
    }
    setBusy(true);
    setProgress(0);
    setError(null);
    try {
      await uploadListeningAudio(task.id, file, null, setProgress);
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
      }
      await onChanged();
    } catch (cause) {
      setError(apiErrorMessage(cause, "Die Audiodatei konnte nicht hochgeladen werden."));
    } finally {
      setBusy(false);
      setProgress(null);
    }
  }

  async function togglePreview() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
      return;
    }
    if (!task) return;
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

  return (
    <article className="space-y-3 rounded-xl border border-[var(--admin-border)] p-3 sm:p-4" data-testid="a2-audio-slot">
      <input
        ref={fileInput}
        type="file"
        accept={AUDIO_ACCEPT}
        className="hidden"
        aria-label={`Audiodatei für ${material.source_name} auswählen`}
        onChange={(event) => void uploadFile(event.target.files?.[0])}
      />
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]">
            <FileAudio2 size={16} className="shrink-0 text-[var(--admin-primary)]" />
            <span>Audio {material.slot_number}: {material.source_name}</span>
          </h4>
          <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
            {task
              ? `Hören-Aufgabe: ${task.title} · ${task.question_count} Fragen${task.key_missing ? ` · ${task.key_missing} Antwortschlüssel fehlen` : ""}`
              : "Noch keiner Hören-Aufgabe zugeordnet"}
          </p>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${status === "ok" ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-warning)]/10 text-[var(--admin-warning)]"}`}>
          {status === "ok" ? "Audio vorhanden" : status === "external" ? "Externe Audioquelle" : task?.file_status === "missing" ? "Datei fehlt" : "Nicht hochgeladen"}
        </span>
      </div>

      {material.format_matches === false && (
        <p role="status" className="text-xs font-medium text-[var(--admin-warning)]">
          Gespeichertes Audioformat entspricht nicht dem Sollformat {material.expected_format}.
        </p>
      )}

      {task?.audio_original_name && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--admin-text-secondary)]">
          <span className="break-all">Datei: {task.audio_original_name}</span>
          <span>Format: {task.audio_format ?? material.expected_format}</span>
          <span>Größe: {formatBytes(lessonTasks.find((item) => item.id === task.id)?.size_bytes ?? null)}</span>
        </div>
      )}

      {previewUrl && (
        <audio controls preload="none" src={previewUrl} className="w-full" aria-label={`Audio ${material.slot_number} anhören`} />
      )}

      {!task ? (
        <div className="flex flex-wrap gap-2">
          {availableTasks.length > 0 && (
            <>
              <AdminSelect
                value={selectedTask}
                onChange={(event) => setSelectedTask(event.target.value)}
                aria-label={`Hören-Aufgabe für Audio ${material.slot_number} auswählen`}
                className="min-w-52"
              >
                <option value="">Vorhandene Aufgabe wählen</option>
                {availableTasks.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
              </AdminSelect>
              <AdminButton size="sm" variant="secondary" disabled={!selectedTask || busy} onClick={() => void attachTask()}>
                {busy ? <LoaderCircle size={14} className="animate-spin" /> : <Link2 size={14} />}
                Aufgabe verbinden
              </AdminButton>
            </>
          )}
          <AdminButton size="sm" disabled={busy} onClick={() => void createTask()}>
            {busy ? <LoaderCircle size={14} className="animate-spin" /> : <Check size={14} />}
            Leere Aufgabe anlegen
          </AdminButton>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            <AdminButton size="sm" variant="secondary" disabled={busy || status !== "ok"} onClick={() => void togglePreview()}>
              {busy && !progress ? <LoaderCircle size={14} className="animate-spin" /> : <Play size={14} />}
              {previewUrl ? "Player schließen" : "Audio anhören"}
            </AdminButton>
            <AdminButton size="sm" disabled={busy} onClick={() => fileInput.current?.click()}>
              {busy && progress !== null ? <LoaderCircle size={14} className="animate-spin" /> : <Upload size={14} />}
              {status === "ok" ? "Audio ersetzen" : "Audio hochladen"}
            </AdminButton>
            <span className="self-center text-xs text-[var(--admin-text-muted)]">Sollformat: {material.expected_format} · max. 100 MB</span>
          </div>
          {progress !== null && (
            <div role="status" className="space-y-1">
              <p className="text-xs text-[var(--admin-text-muted)]">Upload läuft … {progress}%</p>
              <div className="h-1.5 overflow-hidden rounded-full bg-[var(--admin-border)]">
                <div className="h-full bg-[var(--admin-primary)]" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}
        </div>
      )}
      {error && <p role="alert" className="text-sm text-[var(--admin-danger)]">{error}</p>}
    </article>
  );
}

export default function A2ListeningManagement({ mediaItems }: Props) {
  const queryClient = useQueryClient();
  const overview = useQuery({
    queryKey: ["media-mgmt", "a2-listening"],
    queryFn: getA2ListeningOverview,
  });

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["media-mgmt", "a2-listening"] }),
      queryClient.invalidateQueries({ queryKey: ["media-mgmt", "items"] }),
    ]);
  }

  const data = overview.data;
  const lessons = [...(data?.lessons ?? [])].sort((left, right) => left.lesson_number - right.lesson_number);
  const unassignedCount = lessons.reduce(
    (count, lesson) => count + lesson.expected_materials.filter((material) => !material.listening).length,
    0,
  );
  const lessonMismatch = Boolean(data && (data.actual_lesson_count !== data.expected_lesson_count || lessons.some((lesson) => !lesson.lesson_exists)));
  const extraTaskCount = lessons.reduce((count, lesson) => count + (lesson.other_tasks?.length ?? 0), 0);

  return (
    <section className="space-y-5" data-testid="a2-listening-management">
      <div className={card}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[var(--admin-text-primary)]">Niveau A2 · Hören</h2>
            <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">Unterricht 1–13 · Audiodateien und ihre Hören-Aufgaben verwalten.</p>
          </div>
          <AdminButton
            variant="secondary"
            size="sm"
            disabled={overview.isFetching}
            onClick={() => void Promise.all([
              overview.refetch(),
              queryClient.refetchQueries({ queryKey: ["media-mgmt", "items"] }),
            ])}
          >
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
            <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
              {[
                ["Lektionen", `${data.actual_lesson_count} / ${data.expected_lesson_count}`],
                ["Audio-Slots", data.expected_audio_count],
                ["Aufgabe zugeordnet", data.mapped_audio_count],
                ["Audio hochgeladen", data.uploaded_audio_count],
                ["Formatfehler", data.format_mismatch_count],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl border border-[var(--admin-border)] p-3">
                  <dt className="text-xs text-[var(--admin-text-muted)]">{label}</dt>
                  <dd className="mt-1 text-lg font-bold text-[var(--admin-text-primary)]">{value}</dd>
                </div>
              ))}
            </dl>
            {(lessonMismatch || unassignedCount > 0 || extraTaskCount > 0 || data.format_mismatch_count > 0) && (
              <div role="status" className="mt-4 flex items-start gap-2 rounded-xl bg-[var(--admin-warning)]/10 p-3 text-sm text-[var(--admin-warning)]">
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <p>
                  Konfiguration und LMS-Daten weichen voneinander ab
                  {lessonMismatch ? "; eine oder mehrere A2-Lektionen fehlen" : ""}
                  {unassignedCount ? `; ${unassignedCount} Audio-Slot(s) haben noch keine Aufgabe` : ""}
                  {extraTaskCount ? `; ${extraTaskCount} weitere Hören-Aufgabe(n) bleiben unverändert erhalten` : ""}
                  {data.format_mismatch_count ? `; ${data.format_mismatch_count} Formatfehler` : ""}.
                  {" "}Es wurden keine vorhandenen Aufgaben oder Dateien entfernt.
                </p>
              </div>
            )}
          </>
        )}
      </div>

      {overview.isSuccess && lessons.map((lesson) => {
        const lessonTasks = mediaItems.filter((item) => item.kind === "AUDIO" && item.lesson_id === lesson.lesson_id);
        return (
          <section key={lesson.lesson_number} className={`${card} space-y-4`} data-testid={`a2-lesson-${lesson.lesson_number}`}>
            <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[var(--admin-border)] pb-3">
              <h3 className="text-base font-bold text-[var(--admin-text-primary)]">
                Unterricht {lesson.lesson_number}{lesson.lesson_title ? ` · ${lesson.lesson_title}` : ""}
              </h3>
              <span className="text-xs text-[var(--admin-text-muted)]">
                {lesson.expected_materials.length} Audio-Slot(s)
              </span>
            </div>
            {!lesson.lesson_exists && (
              <p role="status" className="text-sm text-[var(--admin-warning)]">Lektion fehlt in der LMS-Kursstruktur; es wurde nichts angelegt.</p>
            )}
            {lesson.expected_materials.map((material) => (
              <SlotCard
                key={material.key}
                lessonNumber={lesson.lesson_number}
                material={material}
                lessonTasks={lessonTasks}
                onChanged={refresh}
              />
            ))}
            {lesson.expected_materials.length === 0 && (
              <p className="text-sm text-[var(--admin-text-muted)]">Für diese Lektion sind keine Audio-Slots konfiguriert.</p>
            )}
          </section>
        );
      })}
    </section>
  );
}
