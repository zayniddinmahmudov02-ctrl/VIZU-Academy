"use client";

import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Copy, Plus, Sparkles } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { apiErrorMessage, duplicateItem, type AdminWritingTask } from "@/features/admin/services/lesson-skills-admin-service";
import { writingApi } from "@/features/admin/services/writing-service";

import AiTaskFields, { aiFormFrom, aiPayload, DEFAULT_WRITING_RUBRIC, EMPTY_AI_FORM, rubricProblem } from "../lesson-skills/ai-task-fields";

type Writing = AdminWritingTask;

/** ISO timestamp <-> <input type="datetime-local"> (local time). */
function toLocalInput(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

function fromLocalInput(value: string): string | null {
  return value ? new Date(value).toISOString() : null;
}

import LessonPicker from "./lesson-picker";

const EMPTY_FORM = {
  lesson_id: "",
  title: "",
  instruction: "",
  min_words: 30,
  max_words: 150,
  order_index: 1,
  is_published: false,
  helper_words: "",
  image_url: "",
  opens_at: "",
  closes_at: "",
  ai: EMPTY_AI_FORM,
};

export default function WritingManager({ lessonId }: { lessonId?: string }) {
  const queryClient = useQueryClient();
  const { data: rawAll, isLoading } = useCrudList("writings", writingApi);
  const all = rawAll as Writing[] | undefined;
  const { create, update, remove } = useCrudMutations("writings", writingApi, lessonId ? [["admin-lesson-skills", lessonId]] : undefined);
  const [duplicating, setDuplicating] = useState<string | null>(null);

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
      helper_words: item.helper_words ?? "",
      image_url: item.image_url ?? "",
      opens_at: toLocalInput(item.opens_at),
      closes_at: toLocalInput(item.closes_at),
      ai: aiFormFrom(item),
    });
    setError(null);
    setDialogOpen(true);
  }

  async function handleSubmit() {
    setError(null);
    const problem = rubricProblem(form.ai.ai_evaluation_enabled ? form.ai.rubric : null);
    if (problem) {
      setError(problem);
      return;
    }
    if (form.min_words > form.max_words) {
      setError("Min. Wörter darf nicht größer als Max. Wörter sein.");
      return;
    }
    const { lesson_id, ai, helper_words, image_url, opens_at, closes_at, ...rest } = form;
    const payload = {
      ...rest,
      ...aiPayload(ai),
      helper_words: helper_words.trim() || null,
      image_url: image_url.trim() || null,
      opens_at: fromLocalInput(opens_at),
      closes_at: fromLocalInput(closes_at),
    };
    try {
      if (editing) {
        await update.mutateAsync({ id: editing.id, data: payload });
      } else {
        await create.mutateAsync({ ...payload, lesson_id });
      }
      setDialogOpen(false);
    } catch (err) {
      setError(apiErrorMessage(err, "Speichern fehlgeschlagen."));
    }
  }

  async function duplicate(item: Writing) {
    setDuplicating(item.id);
    try {
      await duplicateItem("writings", item.id);
      await queryClient.invalidateQueries({ queryKey: ["writings"] });
      if (lessonId) await queryClient.invalidateQueries({ queryKey: ["admin-lesson-skills", lessonId] });
    } finally {
      setDuplicating(null);
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
      key: "ai",
      header: "Bewertung",
      render: (item) =>
        item.ai_evaluation_enabled ? (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--admin-primary)]">
            <Sparkles size={12} /> KI · {item.max_attempts} Versuche
          </span>
        ) : (
          <span className="text-xs text-[var(--admin-text-muted)]">Lehrkraft</span>
        ),
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
    {
      key: "duplicate",
      header: "",
      render: (item) => (
        <button
          type="button"
          onClick={() => duplicate(item)}
          disabled={duplicating === item.id}
          className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--admin-text-secondary)] hover:text-[var(--admin-text-primary)]"
          title="Duplizieren (Kopie ist verborgen)"
        >
          <Copy size={13} /> Duplizieren
        </button>
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

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Hilfswörter (optional)
            </label>
            <AdminInput
              value={form.helper_words}
              onChange={(e) => setForm({ ...form, helper_words: e.target.value })}
              placeholder="heißen, kommen aus, wohnen in, sprechen"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Bild-URL (optional)
            </label>
            <AdminInput
              value={form.image_url}
              onChange={(e) => setForm({ ...form, image_url: e.target.value })}
              placeholder="https://…"
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
                Geöffnet ab (optional)
              </label>
              <AdminInput type="datetime-local" value={form.opens_at} onChange={(e) => setForm({ ...form, opens_at: e.target.value })} />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
                Geschlossen ab (optional)
              </label>
              <AdminInput type="datetime-local" value={form.closes_at} onChange={(e) => setForm({ ...form, closes_at: e.target.value })} />
            </div>
          </div>

          <AiTaskFields value={form.ai} onChange={(ai) => setForm({ ...form, ai })} defaultRubric={DEFAULT_WRITING_RUBRIC} />

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
