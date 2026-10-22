"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, CircleAlert, Headphones, Pencil, Play, Plus, RefreshCw, Upload } from "lucide-react";

import { AdminButton, AdminInput, AdminPageHeader } from "@/components/admin/admin-ui";
import { apiErrorMessage, type AdminQuestion } from "@/features/admin/services/lesson-skills-admin-service";
import QuestionEditorDialog from "@/features/admin/components/lesson-skills/question-editor-dialog";
import {
  assignA2AudioTask,
  createA2AudioTask,
  getA2AudioBlobUrl,
  getA2AudioOverview,
  updateA2AudioTask,
  uploadA2Audio,
  type A2AudioMaterialSlot,
  type A2AudioTask,
} from "@/features/admin/services/media-management-service";

const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";

function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const audio = document.createElement("audio");
    const done = (duration: number | null) => {
      URL.revokeObjectURL(url);
      resolve(duration);
    };
    audio.preload = "metadata";
    audio.onloadedmetadata = () => done(Number.isFinite(audio.duration) ? Math.round(audio.duration) : null);
    audio.onerror = () => done(null);
    audio.src = url;
  });
}

export default function A2AudioClient() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["a2-audio"], queryFn: getA2AudioOverview });
  const input = useRef<HTMLInputElement>(null);
  const target = useRef<{ key: string; format: string } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [questionsFor, setQuestionsFor] = useState<{ task: A2AudioTask; materialKey: string } | null>(null);
  const [audio, setAudio] = useState<{ label: string; url: string } | null>(null);
  const [titles, setTitles] = useState<Record<string, string>>({});
  const [assignments, setAssignments] = useState<Record<string, string>>({});

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["a2-audio"] });
  }

  async function run(id: string, action: () => Promise<unknown>, success: string) {
    setBusy(id);
    setError(null);
    setNotice(null);
    try {
      await action();
      setNotice(success);
      await refresh();
    } catch (err) {
      setError(apiErrorMessage(err, "Aktion fehlgeschlagen."));
    } finally {
      setBusy(null);
    }
  }

  async function onFile(file: File | undefined) {
    if (input.current) input.current.value = "";
    const current = target.current;
    target.current = null;
    if (!file || !current) return;
    if (!file.name.toLowerCase().endsWith(`.${current.format.toLowerCase()}`)) {
      setError(`Für diesen Platz ist nur ${current.format} erlaubt.`);
      return;
    }
    if (file.size > 100 * 1024 * 1024) {
      setError("Die Datei ist größer als 100 MB.");
      return;
    }
    const duration = await readDuration(file);
    await run(current.key, () => uploadA2Audio(current.key, file, duration), "Audio hochgeladen. Vorversionen bleiben archiviert.");
  }

  async function play(materialKey: string, label: string, archiveId?: string) {
    setError(null);
    try {
      const url = await getA2AudioBlobUrl(materialKey, archiveId);
      setAudio((previous) => {
        if (previous) URL.revokeObjectURL(previous.url);
        return { label, url };
      });
    } catch (err) {
      setError(apiErrorMessage(err, "Audio konnte nicht geladen werden."));
    }
  }

  async function ensureTask(lessonNumber: number, slot: A2AudioMaterialSlot) {
    await run(slot.key, () => createA2AudioTask(lessonNumber, slot.key), "Entwurf angelegt. Audio und vorhandene Fragen können nun ergänzt werden.");
  }

  async function assign(slot: A2AudioMaterialSlot) {
    const listeningId = assignments[slot.key];
    if (!listeningId) return;
    await run(slot.key, () => assignA2AudioTask(slot.key, listeningId), "Vorhandene Aufgabe zugeordnet; Fragen und Antworten bleiben erhalten.");
  }

  async function togglePublished(materialKey: string, task: A2AudioTask) {
    await run(
      materialKey,
      () => updateA2AudioTask(materialKey, { is_published: !task.is_published }),
      task.is_published ? "Aufgabe als Entwurf gespeichert." : "Aufgabe veröffentlicht.",
    );
  }

  return (
    <div className="space-y-6" data-testid="a2-audio-management">
      <Link href="/admin/media-management" className="inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-secondary)] hover:text-[var(--admin-primary)]">
        <ArrowLeft size={15} /> Media Management
      </Link>
      <AdminPageHeader
        title="A2 Audio — Unterricht 1–13"
        description="Audio-Dateien, Aufgaben und Fragen der 13 A2-Unterrichtseinheiten verwalten. Uploads ersetzen keine Fragen und archivieren die vorherige Audiodatei."
      />

      <section className={`${card} space-y-3`} data-testid="a2-audio-summary">
        <div className="flex flex-wrap items-center gap-3">
          <Headphones size={18} className="text-[var(--admin-primary)]" />
          <strong>{query.data?.expected_lesson_count ?? 13} Lektionen · {query.data?.expected_audio_count ?? 28} erwartete Audios</strong>
          <span className="text-sm text-[var(--admin-text-secondary)]">
            {query.data ? `${query.data.mapped_audio_count}/28 zugeordnet · ${query.data.uploaded_audio_count}/28 hochgeladen · ${query.data.format_mismatch_count} Formatabweichungen` : "Wird geladen …"}
          </span>
          <AdminButton className="ml-auto" variant="secondary" disabled={query.isFetching} onClick={() => void query.refetch()}>
            <RefreshCw size={14} /> Aktualisieren
          </AdminButton>
        </div>
        {query.data && (!query.data.lesson_count_matches || !query.data.audio_count_matches) && (
          <p className="flex items-start gap-2 text-sm text-[var(--admin-warning)]" role="status">
            <CircleAlert size={16} className="mt-0.5 shrink-0" />
            Reale LMS-Daten weichen vom Soll ab. Bestehende Aufgaben oder Dateien wurden nicht gelöscht.
          </p>
        )}
        {query.isError && <p className="text-sm text-[var(--admin-danger)]" role="alert">{apiErrorMessage(query.error, "A2-Audios konnten nicht geladen werden.")}</p>}
        {error && <p className="text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
        {notice && <p className="text-sm text-[var(--admin-success)]" role="status">{notice}</p>}
        {audio && (
          <div className="flex flex-wrap items-center gap-3 rounded-xl bg-[var(--admin-hover)] p-3">
            <span className="text-sm font-medium">{audio.label}</span>
            <audio controls src={audio.url} className="min-w-64 flex-1" />
            <AdminButton variant="ghost" size="sm" onClick={() => { URL.revokeObjectURL(audio.url); setAudio(null); }}>Schließen</AdminButton>
          </div>
        )}
      </section>

      <div className="space-y-4">
        {query.data?.lessons.map((lesson) => (
          <section key={lesson.lesson_number} className={`${card} space-y-4`} data-testid="a2-audio-lesson" data-lesson={lesson.lesson_number}>
            <div className="flex flex-wrap items-center gap-2 border-b border-[var(--admin-border)] pb-3">
              <h2 className="text-lg font-bold">Unterricht {lesson.lesson_number}</h2>
              <span className="text-sm text-[var(--admin-text-secondary)]">
                {lesson.expected_materials.filter((slot) => slot.listening?.audio_original_name).length}/{lesson.expected_materials.length} Audios vorhanden
              </span>
              {!lesson.lesson_exists && <span className="text-sm text-[var(--admin-warning)]">Lektion fehlt im LMS</span>}
            </div>
            <div className="space-y-3">
              {lesson.expected_materials.map((slot) => {
                const task = slot.listening;
                const availableTasks = lesson.other_tasks
                  .filter((other) => slot.available_task_ids.includes(other.id))
                  .sort((left, right) =>
                    Number(slot.suggested_task_ids.includes(right.id)) - Number(slot.suggested_task_ids.includes(left.id)),
                  );
                return (
                  <article key={slot.key} className="space-y-3 rounded-xl bg-[var(--admin-hover)] p-3" data-testid="a2-audio-slot" data-material={slot.key}>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="min-w-0 flex-1 font-semibold">{slot.source_name}.{slot.expected_format.toLowerCase()}</span>
                      <span className="rounded-md bg-[var(--admin-card)] px-2 py-1 text-xs">{slot.expected_format}</span>
                      {slot.format_matches === false && <span className="text-xs text-[var(--admin-danger)]">Formatabweichung</span>}
                      {task ? (
                        <>
                          <span className={`text-xs ${task.is_published ? "text-[var(--admin-success)]" : "text-[var(--admin-warning)]"}`}>
                            {task.is_published ? "Faol" : "Draft"}
                          </span>
                          <AdminButton size="sm" variant="secondary" disabled={busy !== null} onClick={() => { target.current = { key: slot.key, format: slot.expected_format }; input.current?.click(); }}>
                            <Upload size={14} /> {task.audio_original_name ? "Almashtirish" : "Yuklash"}
                          </AdminButton>
                          {task.audio_format && <span className="text-xs text-[var(--admin-text-secondary)]">{task.audio_format}</span>}
                          {task.audio_original_name && <span className="max-w-48 truncate text-xs text-[var(--admin-text-secondary)]" title={task.audio_original_name}>{task.audio_original_name}</span>}
                          {task.file_status === "ok" && <AdminButton size="sm" variant="secondary" onClick={() => void play(slot.key, task.audio_original_name ?? task.title)}><Play size={14} /> Tinglash</AdminButton>}
                          <AdminButton size="sm" variant="secondary" onClick={() => setQuestionsFor({ task, materialKey: slot.key })}>Savollar ({task.question_count})</AdminButton>
                          <AdminButton size="sm" variant={task.is_published ? "ghost" : "primary"} disabled={busy !== null} onClick={() => void togglePublished(slot.key, task)}>
                            {task.is_published ? "Draft qilish" : <><Check size={14} /> Faollashtirish</>}
                          </AdminButton>
                        </>
                      ) : (
                        <AdminButton size="sm" disabled={busy !== null || !lesson.lesson_exists} onClick={() => void ensureTask(lesson.lesson_number, slot)}>
                          <Plus size={14} /> Bo‘sh slot yaratish
                        </AdminButton>
                      )}
                    </div>
                    {task && (
                      <>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--admin-text-secondary)]">
                          <span>{task.question_count} savol · {task.key_missing} javob kaliti yo‘q</span>
                          <span>·</span>
                          <AdminInput
                            className="h-8 max-w-64"
                            aria-label="Audio material nomi"
                            value={titles[slot.key] ?? task.title}
                            onChange={(event) => setTitles((current) => ({ ...current, [slot.key]: event.target.value }))}
                          />
                          <AdminButton
                            size="sm"
                            variant="ghost"
                            disabled={busy !== null || !(titles[slot.key] ?? task.title).trim() || (titles[slot.key] ?? task.title) === task.title}
                            onClick={() => void run(slot.key, () => updateA2AudioTask(slot.key, { title: (titles[slot.key] ?? task.title).trim() }), "Nomi saqlandi.")}
                          >
                            <Pencil size={13} /> Nomni saqlash
                          </AdminButton>
                        </div>
                        {task.archive.length > 0 && (
                          <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--admin-text-secondary)]">
                            <span>Arxivlangan versiyalar:</span>
                            {task.archive.map((version, index) => (
                              <AdminButton key={version.id} size="sm" variant="ghost" onClick={() => void play(slot.key, version.original_name ?? `Vorversion ${index + 1}`, version.id)}>
                                <Play size={12} /> {version.original_name ?? `Vorversion ${index + 1}`}
                              </AdminButton>
                            ))}
                          </div>
                        )}
                        {task.extra_audio_tracks.length > 0 && (
                          <p className="text-xs text-[var(--admin-warning)]">
                            {task.extra_audio_tracks.length} zusätzliche Alt-Audiospuren bleiben unverändert und zählen nicht als separate Soll-Materialien.
                          </p>
                        )}
                      </>
                    )}
                    {!task && slot.available_task_ids.length > 0 && (
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs text-[var(--admin-text-secondary)]">Vorhandene A2-Aufgabe manuell zuordnen (Fragen bleiben erhalten):</span>
                        <select
                          className="h-9 rounded-lg border border-[var(--admin-border)] bg-[var(--admin-card)] px-2 text-sm"
                          aria-label="Vorhandene A2-Aufgabe wählen"
                          value={assignments[slot.key] ?? ""}
                          onChange={(event) => setAssignments((current) => ({ ...current, [slot.key]: event.target.value }))}
                        >
                          <option value="">Aufgabe wählen</option>
                          {availableTasks.map((other) => (
                            <option key={other.id} value={other.id}>
                              {other.title} · {other.audio_original_name ?? "keine Datei"} · {other.question_count} Fragen
                              {slot.suggested_task_ids.includes(other.id) ? " · Dateiname passt" : ""}
                            </option>
                          ))}
                        </select>
                        <AdminButton size="sm" variant="secondary" disabled={busy !== null || !assignments[slot.key]} onClick={() => void assign(slot)}>Zuordnen</AdminButton>
                      </div>
                    )}
                  </article>
                );
              })}
              {lesson.other_tasks.length > 0 && (
                <p className="text-xs text-[var(--admin-text-muted)]">
                  {lesson.other_tasks.length} weitere, keinem Soll-Audio zugeordnete Hören-Aufgabe(n) bleiben unverändert.
                </p>
              )}
            </div>
          </section>
        ))}
      </div>

      <input ref={input} type="file" className="hidden" accept=".mp3,.m4a,audio/mpeg,audio/mp4,audio/x-m4a" onChange={(event) => void onFile(event.target.files?.[0])} data-testid="a2-audio-upload" />
      {questionsFor && (
        <QuestionEditorDialog
          key={questionsFor.task.id}
          open
          onOpenChange={(open) => !open && setQuestionsFor(null)}
          kind="listenings"
          ownerId={questionsFor.task.id}
          title={questionsFor.task.title}
          initial={questionsFor.task.questions as AdminQuestion[]}
          onSaved={() => { void refresh(); }}
        />
      )}
    </div>
  );
}
