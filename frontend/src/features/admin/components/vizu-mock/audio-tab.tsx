"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Music, Pencil, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel } from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FileUploadField from "@/components/admin/file-upload-field";
import FormDialog from "@/components/admin/form-dialog";
import {
  createVizuMockAudio,
  deleteVizuMockAudio,
  listVizuMockAudio,
  updateVizuMockAudio,
} from "@/features/admin/services/vizu-mock-admin-service";
import type { VizuMockAudio } from "@/features/admin/types/vizu-mock-admin.types";

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  const mm = Math.floor(seconds / 60);
  const ss = seconds % 60;
  return `${mm}:${String(ss).padStart(2, "0")}`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
}

interface FormState {
  title: string;
  audio_url: string;
  duration_seconds: string;
}

const EMPTY_FORM: FormState = { title: "", audio_url: "", duration_seconds: "" };

export default function VizuMockAudioTab() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<VizuMockAudio | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [deleteTarget, setDeleteTarget] = useState<VizuMockAudio | null>(null);

  const { data: audios, isLoading } = useQuery({
    queryKey: ["vizu-mock-admin-audio"],
    queryFn: listVizuMockAudio,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-audio"] });

  const createMutation = useMutation({
    mutationFn: () =>
      createVizuMockAudio({
        title: form.title,
        audio_url: form.audio_url,
        duration_seconds: form.duration_seconds ? Number(form.duration_seconds) : null,
      }),
    onSuccess: () => {
      invalidate();
      closeDialog();
    },
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      updateVizuMockAudio(editing!.id, {
        title: form.title,
        audio_url: form.audio_url,
        duration_seconds: form.duration_seconds ? Number(form.duration_seconds) : null,
      }),
    onSuccess: () => {
      invalidate();
      closeDialog();
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (audio: VizuMockAudio) => updateVizuMockAudio(audio.id, { is_active: !audio.is_active }),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteVizuMockAudio(id),
    onSuccess: () => {
      invalidate();
      setDeleteTarget(null);
    },
  });

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setDialogOpen(true);
  }

  function openEdit(audio: VizuMockAudio) {
    setEditing(audio);
    setForm({
      title: audio.title,
      audio_url: audio.audio_url,
      duration_seconds: audio.duration_seconds !== null ? String(audio.duration_seconds) : "",
    });
    setDialogOpen(true);
  }

  function closeDialog() {
    setDialogOpen(false);
    setEditing(null);
    setForm(EMPTY_FORM);
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-[var(--admin-text-primary)]">Hören-Audios</h2>
          <p className="mt-0.5 text-sm text-[var(--admin-text-secondary)]">
            Audiodateien für zukünftige Hören-Aufgaben hochladen und verwalten.
          </p>
        </div>
        <AdminButton onClick={openCreate}>
          <Plus size={15} />
          Audio hochladen
        </AdminButton>
      </div>

      {!isLoading && (!audios || audios.length === 0) && (
        <AdminEmptySection
          icon={Music}
          title="Noch keine Hören-Audios hinzugefügt"
          description="Laden Sie die erste Audiodatei hoch, um sie später einer Hören-Aufgabe zuzuordnen."
        />
      )}

      {(isLoading || (audios && audios.length > 0)) && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading &&
            Array.from({ length: 3 }).map((_, i) => (
              <AdminCard key={i} className="h-36 animate-pulse">
                <div />
              </AdminCard>
            ))}

          {audios?.map((audio) => (
            <AdminCard key={audio.id} className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate font-semibold text-[var(--admin-text-primary)]">{audio.title}</p>
                  <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">
                    {formatDuration(audio.duration_seconds)} · {formatDate(audio.created_at)}
                  </p>
                </div>
                <span
                  className={
                    audio.is_active
                      ? "shrink-0 rounded-full bg-[var(--admin-success,#22c55e)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-success,#22c55e)]"
                      : "shrink-0 rounded-full bg-[var(--admin-text-muted)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-text-muted)]"
                  }
                >
                  {audio.is_active ? "Aktiv" : "Inaktiv"}
                </span>
              </div>

              <audio controls src={audio.audio_url} className="h-9 w-full" />

              <div className="mt-auto flex items-center gap-1.5">
                <AdminButton variant="secondary" size="sm" onClick={() => openEdit(audio)}>
                  <Pencil size={13} />
                  Bearbeiten
                </AdminButton>
                <AdminButton
                  variant="secondary"
                  size="sm"
                  onClick={() => toggleActiveMutation.mutate(audio)}
                  disabled={toggleActiveMutation.isPending}
                >
                  {audio.is_active ? "Deaktivieren" : "Aktivieren"}
                </AdminButton>
                <AdminButton variant="danger" size="sm" onClick={() => setDeleteTarget(audio)}>
                  <Trash2 size={13} />
                </AdminButton>
              </div>
            </AdminCard>
          ))}
        </div>
      )}

      <FormDialog
        open={dialogOpen}
        onOpenChange={(open) => !open && closeDialog()}
        title={editing ? "Audio bearbeiten" : "Audio hochladen"}
        footer={
          <>
            <AdminButton variant="ghost" onClick={closeDialog} disabled={isSaving}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={() => (editing ? updateMutation.mutate() : createMutation.mutate())}
              disabled={isSaving || !form.title || !form.audio_url}
            >
              {isSaving ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <AdminLabel>Titel</AdminLabel>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="z. B. Hören Teil 1 – A1"
            />
          </div>

          <FileUploadField
            label="Audiodatei"
            value={form.audio_url || null}
            onChange={(url) => setForm((f) => ({ ...f, audio_url: url }))}
            folder="audio"
            accept="audio/*"
          />

          <div>
            <AdminLabel>Dauer (Sekunden, optional)</AdminLabel>
            <AdminInput
              type="number"
              min={0}
              value={form.duration_seconds}
              onChange={(e) => setForm((f) => ({ ...f, duration_seconds: e.target.value }))}
              placeholder="z. B. 95"
            />
          </div>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Audio löschen"
        description={`Möchten Sie "${deleteTarget?.title}" wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.`}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
