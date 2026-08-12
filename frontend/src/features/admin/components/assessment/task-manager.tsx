"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Eye, Pencil, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  createTask,
  deleteTask,
  listTasks,
  reorderTasks,
  updateTask,
} from "@/features/admin/services/assessment-service";
import { TASK_TYPE_LABELS, TASK_TYPES, type AssessmentTask, type TaskType } from "@/features/admin/types/assessment.types";

const STATUS_STYLE: Record<string, string> = {
  DRAFT: "bg-[var(--admin-hover)] text-[var(--admin-text-muted)]",
  PUBLISHED: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]",
  ARCHIVED: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
};

const EMPTY_FORM = { title: "", instructions: "", task_type: "MULTIPLE_CHOICE" as TaskType, max_points: 0 };

/** Reusable across both the ModelTest editor and (future) Course Lesson
 * editor — takes only a resolved sectionId (the shared AssessmentSection
 * a Kompetenz maps to; see get-or-create-kompetenz endpoints) and knows
 * nothing about which surface it's mounted in. Generic fields only
 * (title/instructions/type/points/status) — task-type-specific editors
 * (rich cloze-text builder, option lists, audio upload, ...) are a
 * separate, later plug-in point, not implemented here. */
export default function TaskManager({ sectionId }: { sectionId: string }) {
  const queryClient = useQueryClient();
  const queryKey = ["assessment-tasks", sectionId];
  const { data: tasks, isLoading } = useQuery({ queryKey, queryFn: () => listTasks(sectionId) });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<AssessmentTask | null>(null);
  const [previewing, setPreviewing] = useState<AssessmentTask | null>(null);
  const [deleting, setDeleting] = useState<AssessmentTask | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deletingPending, setDeletingPending] = useState(false);

  const sorted = [...(tasks ?? [])].sort((a, b) => a.sort_order - b.sort_order);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(task: AssessmentTask) {
    setEditing(task);
    setForm({
      title: task.title,
      instructions: task.instructions ?? "",
      task_type: task.task_type,
      max_points: task.max_points,
    });
    setError(null);
    setDialogOpen(true);
  }

  async function handleSubmit() {
    setError(null);
    setSaving(true);
    try {
      if (editing) {
        await updateTask(editing.id, {
          title: form.title,
          instructions: form.instructions || null,
          max_points: form.max_points,
        });
      } else {
        await createTask(sectionId, {
          task_type: form.task_type,
          title: form.title,
          instructions: form.instructions || null,
          max_points: form.max_points,
          sort_order: sorted.length + 1,
        });
      }
      queryClient.invalidateQueries({ queryKey });
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish(task: AssessmentTask) {
    const nextStatus = task.status === "PUBLISHED" ? "DRAFT" : "PUBLISHED";
    await updateTask(task.id, { status: nextStatus });
    queryClient.invalidateQueries({ queryKey });
  }

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= sorted.length) return;
    const reordered = [...sorted];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    await reorderTasks(sectionId, reordered.map((t) => t.id));
    queryClient.invalidateQueries({ queryKey });
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold text-[var(--admin-text-primary)]">Aufgaben</h4>
        <AdminButton size="sm" variant="secondary" onClick={openCreate}>
          <Plus size={14} />
          Aufgabe hinzufügen
        </AdminButton>
      </div>

      {isLoading && <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {!isLoading && sorted.length === 0 && (
        <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Aufgaben angelegt.</p>
      )}

      <div className="space-y-2.5">
        {sorted.map((task, index) => (
          <AdminCard key={task.id} className="!p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-[var(--admin-text-primary)]">
                  {index + 1}. {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}
                </p>
                {task.title && <p className="mt-0.5 truncate text-sm text-[var(--admin-text-secondary)]">{task.title}</p>}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className="text-xs text-[var(--admin-text-muted)]">{task.max_points} Punkte</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_STYLE[task.status]}`}>
                    {task.status}
                  </span>
                </div>
              </div>

              <div className="flex shrink-0 flex-col items-end gap-1">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => move(index, -1)}
                    disabled={index === 0}
                    aria-label="Nach oben"
                    className="flex h-6 w-6 items-center justify-center rounded text-[var(--admin-text-muted)] hover:bg-[var(--admin-hover)] disabled:opacity-30"
                  >
                    <ArrowUp size={13} />
                  </button>
                  <button
                    onClick={() => move(index, 1)}
                    disabled={index === sorted.length - 1}
                    aria-label="Nach unten"
                    className="flex h-6 w-6 items-center justify-center rounded text-[var(--admin-text-muted)] hover:bg-[var(--admin-hover)] disabled:opacity-30"
                  >
                    <ArrowDown size={13} />
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-[var(--admin-border)] pt-3">
              <AdminButton size="sm" variant="ghost" onClick={() => openEdit(task)}>
                <Pencil size={13} />
                Bearbeiten
              </AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={() => setPreviewing(task)}>
                <Eye size={13} />
                Vorschau
              </AdminButton>
              <AdminButton size="sm" variant={task.status === "PUBLISHED" ? "secondary" : "primary"} onClick={() => togglePublish(task)}>
                {task.status === "PUBLISHED" ? "Auf Entwurf setzen" : "Veröffentlichen"}
              </AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={() => setDeleting(task)}>
                <Trash2 size={13} />
                Löschen
              </AdminButton>
            </div>
          </AdminCard>
        ))}
      </div>

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Aufgabe bearbeiten" : "Neue Aufgabe"}
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton onClick={handleSubmit} disabled={saving || !form.title}>
              {saving ? "Wird gespeichert..." : "Als Entwurf speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          {!editing && (
            <div>
              <AdminLabel>Aufgabentyp</AdminLabel>
              <AdminSelect
                value={form.task_type}
                onChange={(e) => setForm({ ...form, task_type: e.target.value as TaskType })}
              >
                {TASK_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {TASK_TYPE_LABELS[type]}
                  </option>
                ))}
              </AdminSelect>
            </div>
          )}

          <div>
            <AdminLabel>Titel</AdminLabel>
            <AdminInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Lesen Sie den Text..." />
          </div>

          <div>
            <AdminLabel>Anweisung (optional)</AdminLabel>
            <AdminTextarea
              rows={3}
              value={form.instructions}
              onChange={(e) => setForm({ ...form, instructions: e.target.value })}
            />
          </div>

          <div>
            <AdminLabel>Punkte</AdminLabel>
            <AdminInput
              type="number"
              value={form.max_points}
              onChange={(e) => setForm({ ...form, max_points: Number(e.target.value) })}
            />
          </div>
        </div>
      </FormDialog>

      <FormDialog
        open={!!previewing}
        onOpenChange={(open) => !open && setPreviewing(null)}
        title="Vorschau"
        footer={
          <AdminButton variant="ghost" onClick={() => setPreviewing(null)}>
            Schließen
          </AdminButton>
        }
      >
        {previewing && (
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
              {TASK_TYPE_LABELS[previewing.task_type] ?? previewing.task_type}
            </p>
            <p className="text-lg font-semibold text-[var(--admin-text-primary)]">{previewing.title}</p>
            {previewing.instructions && (
              <p className="text-sm text-[var(--admin-text-secondary)]">{previewing.instructions}</p>
            )}
            <p className="text-xs text-[var(--admin-text-muted)]">
              {previewing.max_points} Punkte · {previewing.questions.length} Frage(n) · Status: {previewing.status}
            </p>
          </div>
        )}
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Aufgabe löschen"
        description={`"${deleting?.title || "Diese Aufgabe"}" wird dauerhaft gelöscht.`}
        isPending={deletingPending}
        onConfirm={async () => {
          if (!deleting) return;
          setDeletingPending(true);
          try {
            await deleteTask(deleting.id);
            queryClient.invalidateQueries({ queryKey });
          } finally {
            setDeletingPending(false);
            setDeleting(null);
          }
        }}
      />
    </div>
  );
}
