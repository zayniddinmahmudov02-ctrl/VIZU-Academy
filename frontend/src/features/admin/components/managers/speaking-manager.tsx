"use client";

import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Copy, Plus, Sparkles } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { apiErrorMessage, duplicateItem, type AdminSpeakingTask } from "@/features/admin/services/lesson-skills-admin-service";
import { speakingApi } from "@/features/admin/services/speaking-service";

import AiTaskFields, { aiFormFrom, aiPayload, DEFAULT_SPEAKING_RUBRIC, EMPTY_AI_FORM, rubricProblem } from "../lesson-skills/ai-task-fields";

type Speaking = AdminSpeakingTask;

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
  min_duration_seconds: 0,
  ai: EMPTY_AI_FORM,
};

export default function SpeakingManager({ lessonId }: { lessonId?: string }) {
  const queryClient = useQueryClient();
  const { data: rawAll, isLoading } = useCrudList("speakings", speakingApi);
  const all = rawAll as Speaking[] | undefined;
  const { create, update, remove } = useCrudMutations("speakings", speakingApi, lessonId ? [["admin-lesson-skills", lessonId]] : undefined);
  const [duplicating, setDuplicating] = useState<string | null>(null);

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
      min_duration_seconds: item.min_duration_seconds ?? 0,
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
    if (form.min_duration_seconds && form.speaking_time && form.min_duration_seconds > form.speaking_time) {
      setError("Mindestdauer darf nicht größer als die Sprechzeit sein.");
      return;
    }
    const { lesson_id, ai, ...rest } = form;
    const payload = { ...rest, ...aiPayload(ai) };
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

  async function duplicate(item: Speaking) {
    setDuplicating(item.id);
    try {
      await duplicateItem("speakings", item.id);
      await queryClient.invalidateQueries({ queryKey: ["speakings"] });
      if (lessonId) await queryClient.invalidateQueries({ queryKey: ["admin-lesson-skills", lessonId] });
    } finally {
      setDuplicating(null);
    }
  }

  const columns: DataTableColumn<Speaking>[] = [
    { key: "title", header: "Titel", render: (item) => item.title },
    { key: "topic", header: "Thema", render: (item) => item.topic },
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

          <div className="w-48">
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Mindestdauer (Sek.)
            </label>
            <AdminInput
              type="number"
              min={0}
              value={form.min_duration_seconds}
              onChange={(e) => setForm({ ...form, min_duration_seconds: Number(e.target.value) })}
            />
          </div>

          <AiTaskFields value={form.ai} onChange={(ai) => setForm({ ...form, ai })} defaultRubric={DEFAULT_SPEAKING_RUBRIC} />

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
