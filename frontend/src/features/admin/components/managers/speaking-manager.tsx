"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { speakingApi } from "@/features/admin/services/speaking-service";
import type { Speaking } from "@/features/admin/types/content.types";

import LessonPicker from "./lesson-picker";

const EMPTY_FORM = {
  lesson_id: "",
  title: "",
  topic: "",
  instruction: "",
  sample_answer: "",
  keywords: "",
  preparation_time: 15,
  speaking_time: 90,
  order_index: 1,
  is_published: false,
};

export default function SpeakingManager({ lessonId }: { lessonId?: string }) {
  const { data: all, isLoading } = useCrudList("speakings", speakingApi);
  const { create, update, remove } = useCrudMutations("speakings", speakingApi);

  const data = useMemo(
    () => (lessonId ? (all ?? []).filter((s) => s.lesson_id === lessonId) : all),
    [all, lessonId],
  );

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Speaking | null>(null);
  const [deleting, setDeleting] = useState<Speaking | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, lesson_id: lessonId ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Speaking) {
    setEditing(item);
    setForm({
      lesson_id: item.lesson_id,
      title: item.title,
      topic: item.topic,
      instruction: item.instruction,
      sample_answer: item.sample_answer ?? "",
      keywords: item.keywords ?? "",
      preparation_time: item.preparation_time,
      speaking_time: item.speaking_time,
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

  const columns: DataTableColumn<Speaking>[] = [
    { key: "title", header: "Titel", render: (item) => item.title },
    { key: "topic", header: "Thema", render: (item) => item.topic },
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
          Neue Sprechübung
        </AdminButton>
      </div>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Sprechübungen angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Sprechübung bearbeiten" : "Neue Sprechübung"}
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
                !form.topic ||
                !form.instruction ||
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
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Thema
            </label>
            <AdminInput
              value={form.topic}
              onChange={(e) => setForm({ ...form, topic: e.target.value })}
              placeholder="Meine Familie"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Hinweise / Anweisungen
            </label>
            <AdminTextarea
              rows={3}
              value={form.instruction}
              onChange={(e) => setForm({ ...form, instruction: e.target.value })}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Schlüsselwörter (kommagetrennt)
            </label>
            <AdminInput
              value={form.keywords}
              onChange={(e) => setForm({ ...form, keywords: e.target.value })}
              placeholder="Vater, Mutter, Geschwister"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Musterantwort (optional)
            </label>
            <AdminTextarea
              rows={2}
              value={form.sample_answer}
              onChange={(e) => setForm({ ...form, sample_answer: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
                Vorbereitungszeit (Sek.)
              </label>
              <AdminInput
                type="number"
                value={form.preparation_time}
                onChange={(e) => setForm({ ...form, preparation_time: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
                Sprechzeit (Sek.)
              </label>
              <AdminInput
                type="number"
                value={form.speaking_time}
                onChange={(e) => setForm({ ...form, speaking_time: Number(e.target.value) })}
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
        title="Sprechübung löschen"
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
