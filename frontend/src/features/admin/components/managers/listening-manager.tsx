"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FileUploadField from "@/components/admin/file-upload-field";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { listeningApi } from "@/features/admin/services/listening-service";
import type { Listening } from "@/features/admin/types/content.types";

import LessonPicker from "./lesson-picker";

const EMPTY_FORM = {
  lesson_id: "",
  title: "",
  audio_url: "",
  transcript: "",
  order_index: 1,
  is_published: false,
};

export default function ListeningManager({ lessonId }: { lessonId?: string }) {
  const { data: all, isLoading } = useCrudList("listenings", listeningApi);
  const { create, update, remove } = useCrudMutations("listenings", listeningApi);

  const data = useMemo(
    () => (lessonId ? (all ?? []).filter((l) => l.lesson_id === lessonId) : all),
    [all, lessonId],
  );

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Listening | null>(null);
  const [deleting, setDeleting] = useState<Listening | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, lesson_id: lessonId ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Listening) {
    setEditing(item);
    setForm({
      lesson_id: item.lesson_id,
      title: item.title,
      audio_url: item.audio_url,
      transcript: item.transcript ?? "",
      order_index: item.order_index,
      is_published: item.is_published,
    });
    setError(null);
    setDialogOpen(true);
  }

  async function handleSubmit() {
    setError(null);
    try {
      if (editing) {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { lesson_id: _lessonId, ...updateData } = form;
        await update.mutateAsync({ id: editing.id, data: updateData });
      } else {
        await create.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  const columns: DataTableColumn<Listening>[] = [
    { key: "title", header: "Titel", render: (item) => item.title },
    {
      key: "audio",
      header: "Audio",
      render: (item) => (item.audio_url ? "✓" : "—"),
    },
    {
      key: "is_published",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            item.is_published
              ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
              : "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.is_published ? "Veröffentlicht" : "Entwurf"}
        </span>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <AdminButton onClick={openCreate}>
          <Plus size={16} />
          Neue Hörübung
        </AdminButton>
      </div>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Hörübungen angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Hörübung bearbeiten" : "Neue Hörübung"}
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={
                create.isPending ||
                update.isPending ||
                !form.title ||
                !form.audio_url ||
                !form.lesson_id
              }
            >
              {create.isPending || update.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          {!lessonId && !editing && (
            <LessonPicker
              value={form.lesson_id}
              onChange={(id) => setForm({ ...form, lesson_id: id })}
            />
          )}

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Titel
            </label>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Im Restaurant"
            />
          </div>

          <FileUploadField
            label="Audio"
            folder="audio"
            accept="audio/*"
            value={form.audio_url || null}
            onChange={(url) => setForm({ ...form, audio_url: url })}
          />

          {form.audio_url && (
            <audio controls src={form.audio_url} className="w-full">
              <track kind="captions" />
            </audio>
          )}

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Transkript (optional)
            </label>
            <AdminTextarea
              rows={4}
              value={form.transcript}
              onChange={(e) => setForm({ ...form, transcript: e.target.value })}
            />
          </div>

          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox
              checked={form.is_published}
              onCheckedChange={(checked) => setForm({ ...form, is_published: checked })}
            />
            <span className="text-sm text-[var(--admin-text-secondary)]">Veröffentlicht</span>
          </label>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Hörübung löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht.`}
        isPending={remove.isPending}
        onConfirm={async () => {
          if (!deleting) return;
          await remove.mutateAsync(deleting.id);
          setDeleting(null);
        }}
      />
    </div>
  );
}
