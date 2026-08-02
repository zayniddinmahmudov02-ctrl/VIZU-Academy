"use client";

import { useMemo, useState } from "react";
import { HelpCircle, Plus } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import RichTextEditor from "@/components/admin/rich-text-editor";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { readingsApi } from "@/features/admin/services/reading-service";
import type { Reading } from "@/features/admin/types/content.types";

import LessonPicker from "./lesson-picker";
import ReadingQuestionsEditor from "./reading-questions-editor";

const EMPTY_FORM = { lesson_id: "", title: "", content: "", order_index: 1, is_published: false };

export default function ReadingManager({ lessonId }: { lessonId?: string }) {
  const { data: all, isLoading } = useCrudList("readings", readingsApi);
  const { create, update, remove } = useCrudMutations("readings", readingsApi);

  const data = useMemo(
    () => (lessonId ? (all ?? []).filter((r) => r.lesson_id === lessonId) : all),
    [all, lessonId],
  );

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Reading | null>(null);
  const [deleting, setDeleting] = useState<Reading | null>(null);
  const [questionsFor, setQuestionsFor] = useState<Reading | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, lesson_id: lessonId ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Reading) {
    setEditing(item);
    setForm({
      lesson_id: item.lesson_id,
      title: item.title,
      content: item.content,
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

  const columns: DataTableColumn<Reading>[] = [
    { key: "title", header: "Titel", render: (item) => item.title },
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
    {
      key: "questions",
      header: "",
      render: (item) => (
        <button
          onClick={() => setQuestionsFor(item)}
          className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-[var(--admin-primary)] hover:bg-[var(--admin-primary)]/10"
        >
          <HelpCircle size={13} />
          Fragen verwalten
        </button>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <AdminButton onClick={openCreate}>
          <Plus size={16} />
          Neuer Lesetext
        </AdminButton>
      </div>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Lesetexte angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Lesetext bearbeiten" : "Neuer Lesetext"}
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
              Titel
            </label>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Ein Tag in Berlin"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Text
            </label>
            <RichTextEditor
              value={form.content}
              onChange={(html) => setForm({ ...form, content: html })}
              placeholder="Lesetext mit Absätzen und Bildern..."
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

      <FormDialog
        open={!!questionsFor}
        onOpenChange={(open) => !open && setQuestionsFor(null)}
        title={`Fragen — ${questionsFor?.title ?? ""}`}
        description="Multiple-Choice-Fragen zu diesem Lesetext."
        size="lg"
      >
        {questionsFor && <ReadingQuestionsEditor readingId={questionsFor.id} />}
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Lesetext löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht, inklusive aller Fragen.`}
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
