"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { writingApi } from "@/features/admin/services/writing-service";
import type { Writing } from "@/features/admin/types/content.types";

import LessonPicker from "./lesson-picker";

const EMPTY_FORM = {
  lesson_id: "",
  title: "",
  instruction: "",
  min_words: 30,
  max_words: 150,
  order_index: 1,
  is_published: false,
};

export default function WritingManager({ lessonId }: { lessonId?: string }) {
  const { data: all, isLoading } = useCrudList("writings", writingApi);
  const { create, update, remove } = useCrudMutations("writings", writingApi);

  const data = useMemo(
    () => (lessonId ? (all ?? []).filter((w) => w.lesson_id === lessonId) : all),
    [all, lessonId],
  );

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Writing | null>(null);
  const [deleting, setDeleting] = useState<Writing | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, lesson_id: lessonId ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Writing) {
    setEditing(item);
    setForm({
      lesson_id: item.lesson_id,
      title: item.title,
      instruction: item.instruction,
      min_words: item.min_words,
      max_words: item.max_words,
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

  const columns: DataTableColumn<Writing>[] = [
    { key: "title", header: "Thema", render: (item) => item.title },
    {
      key: "words",
      header: "Wortanzahl",
      render: (item) => `${item.min_words}–${item.max_words}`,
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
          Neues Schreib-Thema
        </AdminButton>
      </div>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Schreib-Themen angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Schreib-Thema bearbeiten" : "Neues Schreib-Thema"}
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={create.isPending || update.isPending || !form.title || !form.lesson_id}
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
              Thema
            </label>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Schreib einen Brief an einen Freund"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Anweisungen
            </label>
            <AdminTextarea
              rows={4}
              value={form.instruction}
              onChange={(e) => setForm({ ...form, instruction: e.target.value })}
              placeholder="Beschreibe, was der Text enthalten soll..."
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
                Min. Wörter
              </label>
              <AdminInput
                type="number"
                value={form.min_words}
                onChange={(e) => setForm({ ...form, min_words: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
                Max. Wörter
              </label>
              <AdminInput
                type="number"
                value={form.max_words}
                onChange={(e) => setForm({ ...form, max_words: Number(e.target.value) })}
              />
            </div>
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
        title="Schreib-Thema löschen"
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
