"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Copy, Eye, EyeOff, ListChecks, Pencil, Play, Plus, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  apiErrorMessage,
  duplicateItem,
  getListeningAudioBlobUrl,
  uploadListeningAudio,
  type AdminHoerenTask,
} from "@/features/admin/services/lesson-skills-admin-service";
import { listeningApi } from "@/features/admin/services/listening-service";

import QuestionEditorDialog from "./question-editor-dialog";
import { ItemCard, PublishBadge, useLessonSkillsOverview } from "./shared";

const EMPTY = { title: "", instruction: "", transcript: "", order_index: 1, is_published: false };
const MAX_BYTES = 25 * 1024 * 1024;
const ACCEPT = ".mp3,.wav,.m4a,audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/x-m4a";

function formatTime(seconds: number | null): string {
  if (!seconds) return "—";
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

/** Duration read from the file in the browser (informational; the server
 * validates type and size). */
function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const audio = new Audio();
    const done = (value: number | null) => {
      URL.revokeObjectURL(url);
      resolve(value);
    };
    audio.preload = "metadata";
    audio.onloadedmetadata = () => done(Number.isFinite(audio.duration) ? Math.round(audio.duration) : null);
    audio.onerror = () => done(null);
    audio.src = url;
  });
}

function AudioPreview({ listeningId, version }: { listeningId: string; version: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const urlRef = useRef<string | null>(null);

  useEffect(() => () => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
  }, []);

  async function load() {
    try {
      const url = await getListeningAudioBlobUrl(listeningId);
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      urlRef.current = url;
      setSrc(url);
    } catch {
      setFailed(true);
    }
  }

  if (failed) return <p className="text-xs text-[var(--admin-danger)]">Audio konnte nicht geladen werden.</p>;
  if (!src) {
    return (
      <AdminButton size="sm" variant="secondary" onClick={load} data-testid="hoeren-preview">
        <Play size={14} /> Anhören
      </AdminButton>
    );
  }
  return <audio key={version} controls src={src} className="w-full max-w-md" />;
}

/** Hören: tasks with privately stored audio (MP3/WAV/M4A ≤ 25 MB),
 * transcript (shown to students only after their first attempt) and
 * auto-graded questions. */
export default function HoerenManager({ lessonId }: { lessonId: string }) {
  const { data, isLoading, refresh } = useLessonSkillsOverview(lessonId);
  const tasks = data?.hoeren ?? [];

  const [editing, setEditing] = useState<AdminHoerenTask | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [questionsFor, setQuestionsFor] = useState<AdminHoerenTask | null>(null);
  const [deleting, setDeleting] = useState<AdminHoerenTask | null>(null);
  const [busy, setBusy] = useState(false);
  const [uploadingId, setUploadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const uploadTarget = useRef<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY, order_index: tasks.length + 1 });
    setError(null);
    setFormOpen(true);
  }

  function openEdit(item: AdminHoerenTask) {
    setEditing(item);
    setForm({
      title: item.title,
      instruction: item.instruction ?? "",
      transcript: item.transcript ?? "",
      order_index: item.order_index,
      is_published: item.is_published,
    });
    setError(null);
    setFormOpen(true);
  }

  async function run(action: () => Promise<unknown>, fallback = "Aktion fehlgeschlagen.") {
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh();
      return true;
    } catch (err) {
      setError(apiErrorMessage(err, fallback));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    const payload = {
      title: form.title.trim(),
      instruction: form.instruction.trim() || null,
      transcript: form.transcript.trim() || null,
      order_index: form.order_index,
      is_published: form.is_published,
    };
    const ok = await run(
      () => (editing ? listeningApi.update(editing.id, payload) : listeningApi.create({ ...payload, lesson_id: lessonId })),
      "Speichern fehlgeschlagen.",
    );
    if (ok) setFormOpen(false);
  }

  function pickFile(listeningId: string) {
    uploadTarget.current = listeningId;
    fileInput.current?.click();
  }

  async function onFile(file: File | undefined) {
    const id = uploadTarget.current;
    if (fileInput.current) fileInput.current.value = "";
    if (!file || !id) return;
    if (!/\.(mp3|wav|m4a)$/i.test(file.name)) {
      setError("Nur MP3, WAV oder M4A.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("Die Datei ist größer als 25 MB.");
      return;
    }
    setUploadingId(id);
    const duration = await readDuration(file);
    await run(() => uploadListeningAudio(id, file, duration), "Upload fehlgeschlagen.");
    setUploadingId(null);
  }

  return (
    <div className="space-y-4" data-testid="admin-hoeren">
      <input ref={fileInput} type="file" accept={ACCEPT} className="hidden" onChange={(e) => onFile(e.target.files?.[0])} data-testid="hoeren-file" />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[var(--admin-text-secondary)]">{tasks.length} Hörtexte · MP3 / WAV / M4A, max. 25 MB, privat gespeichert</p>
        <AdminButton onClick={openCreate} data-testid="hoeren-new">
          <Plus size={16} /> Neue Höraufgabe
        </AdminButton>
      </div>

      {error && !formOpen && <p className="text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {!isLoading && tasks.length === 0 && (
        <p className="rounded-2xl bg-[var(--admin-card)] p-6 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
          Noch keine Höraufgaben in dieser Lektion.
        </p>
      )}

      {tasks.map((item) => {
        const hasAudio = item.has_uploaded_audio || !!item.audio_url;
        return (
          <ItemCard
            key={item.id}
            testId="hoeren-item"
            title={`${item.order_index}. ${item.title}`}
            badge={<PublishBadge published={item.is_published} />}
            meta={
              <>
                {item.questions.length} Fragen · {item.max_points} Punkte · Dauer {formatTime(item.audio_duration_seconds)}
                {item.audio_original_name && <> · {item.audio_original_name}</>}
              </>
            }
            actions={
              <>
                <AdminButton size="sm" variant="secondary" onClick={() => setQuestionsFor(item)} data-testid="hoeren-questions">
                  <ListChecks size={14} /> Fragen
                </AdminButton>
                <AdminButton size="sm" variant="secondary" disabled={uploadingId === item.id} onClick={() => pickFile(item.id)} data-testid="hoeren-upload">
                  <Upload size={14} /> {uploadingId === item.id ? "Lädt hoch..." : item.has_uploaded_audio ? "Audio ersetzen" : "Audio hochladen"}
                </AdminButton>
                <AdminButton size="sm" variant="ghost" onClick={() => openEdit(item)} aria-label="Bearbeiten">
                  <Pencil size={14} />
                </AdminButton>
                <AdminButton
                  size="sm"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => run(() => listeningApi.update(item.id, { is_published: !item.is_published }))}
                  aria-label={item.is_published ? "Verbergen" : "Veröffentlichen"}
                  title={item.is_published ? "Verbergen" : "Veröffentlichen"}
                  data-testid="hoeren-toggle-publish"
                >
                  {item.is_published ? <EyeOff size={14} /> : <Eye size={14} />}
                </AdminButton>
                <AdminButton size="sm" variant="ghost" disabled={busy} onClick={() => run(() => duplicateItem("listenings", item.id))} aria-label="Duplizieren" title="Duplizieren">
                  <Copy size={14} />
                </AdminButton>
                <AdminButton size="sm" variant="ghost" onClick={() => setDeleting(item)} aria-label="Löschen">
                  <Trash2 size={14} />
                </AdminButton>
              </>
            }
          >
            {item.instruction && <p className="text-sm text-[var(--admin-text-secondary)]">{item.instruction}</p>}
            {item.has_uploaded_audio ? (
              <AudioPreview listeningId={item.id} version={`${item.audio_original_name}-${item.audio_duration_seconds}`} />
            ) : item.audio_url ? (
              <audio controls src={item.audio_url} className="w-full max-w-md" />
            ) : null}
            {item.is_published && (!hasAudio || item.questions.length === 0) && (
              <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-400">
                <AlertTriangle size={13} />
                {!hasAudio ? "Veröffentlicht, aber noch ohne Audio — Schüler sehen diese Aufgabe nicht." : "Noch keine Fragen."}
              </p>
            )}
          </ItemCard>
        );
      })}

      <FormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        title={editing ? "Höraufgabe bearbeiten" : "Neue Höraufgabe"}
        description={editing ? undefined : "Nach dem Speichern: Audio hochladen und Fragen anlegen."}
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setFormOpen(false)}>Abbrechen</AdminButton>
            <AdminButton onClick={save} disabled={busy || !form.title.trim()} data-testid="hoeren-save">
              {busy ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Titel</label>
            <AdminInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Anweisung</label>
            <AdminTextarea rows={2} value={form.instruction} onChange={(e) => setForm({ ...form, instruction: e.target.value })} placeholder="Hör zu und beantworte die Fragen." />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Transkript (für Schüler erst nach dem ersten Versuch sichtbar)</label>
            <AdminTextarea rows={6} value={form.transcript} onChange={(e) => setForm({ ...form, transcript: e.target.value })} />
          </div>
          <div className="flex flex-wrap items-end gap-6">
            <div className="w-32">
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Reihenfolge</label>
              <AdminInput type="number" min={1} value={form.order_index} onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })} />
            </div>
            <label className="flex cursor-pointer items-center gap-2.5 pb-2">
              <AdminCheckbox checked={form.is_published} onCheckedChange={(checked) => setForm({ ...form, is_published: checked })} />
              <span className="text-sm text-[var(--admin-text-secondary)]">Veröffentlicht</span>
            </label>
          </div>
        </div>
      </FormDialog>

      {questionsFor && (
        <QuestionEditorDialog
          key={questionsFor.id}
          open
          onOpenChange={(open) => !open && setQuestionsFor(null)}
          kind="listenings"
          ownerId={questionsFor.id}
          title={questionsFor.title}
          initial={questionsFor.questions}
          onSaved={refresh}
        />
      )}

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Höraufgabe löschen"
        description={`"${deleting?.title}" wird mit Audio, Fragen und allen Hör-Ergebnissen der Schüler zu dieser Aufgabe gelöscht. Tipp: stattdessen verbergen.`}
        isPending={busy}
        onConfirm={async () => {
          if (!deleting) return;
          if (await run(() => listeningApi.remove(deleting.id), "Löschen fehlgeschlagen.")) setDeleting(null);
        }}
      />
    </div>
  );
}
