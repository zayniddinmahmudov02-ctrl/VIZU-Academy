"use client";

import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Copy, Plus, Sparkles } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { apiErrorMessage, duplicateItem, type AdminSpeakingTask } from "@/features/admin/services/lesson-skills-admin-service";
import { speakingApi } from "@/features/admin/services/speaking-service";

import AiTaskFields, { aiFormFrom, aiPayload, DEFAULT_SPEAKING_RUBRIC, EMPTY_AI_FORM, rubricProblem } from "../lesson-skills/ai-task-fields";
import { useLevelDefaultRubric } from "../lesson-skills/shared";

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
  response_type: "MONOLOG" as "MONOLOG" | "DIALOG",
  questions: "",
  speech_goal: "",
  ai: EMPTY_AI_FORM,
};

/** kind FRAGE manages the lesson's Frage des Themas voice tasks (same
 * recorder for students, no rubric unless an admin adds one). */
export default function SpeakingManager({ lessonId, kind = "SPRECHEN" }: { lessonId?: string; kind?: "SPRECHEN" | "FRAGE" }) {
  const queryClient = useQueryClient();
  const { data: rawAll, isLoading } = useCrudList("speakings", speakingApi);
  const all = rawAll as Speaking[] | undefined;
  const { create, update, remove } = useCrudMutations("speakings", speakingApi, lessonId ? [["admin-lesson-skills", lessonId]] : undefined);
  const [duplicating, setDuplicating] = useState<string | null>(null);

  const data = useMemo(
    () => (all ?? []).filter((s) => (!lessonId || s.lesson_id === lessonId) && (s.task_kind ?? "SPRECHEN") === kind),
    [all, lessonId, kind],
  );

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Speaking | null>(null);
  const [deleting, setDeleting] = useState<Speaking | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const levelDefault = useLevelDefaultRubric(lessonId, "speaking");

  function openCreate() {
    setEditing(null);
    setForm({
      ...EMPTY_FORM,
      lesson_id: lessonId ?? "",
      ...(kind === "FRAGE" ? { preparation_time: 0, speaking_time: 120, ai: { ...EMPTY_AI_FORM, ai_evaluation_enabled: false } } : {}),
    });
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
      response_type: item.response_type ?? "MONOLOG",
      questions: (item.questions ?? []).join("\n"),
      speech_goal: item.speech_goal ?? "",
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
    const { lesson_id, ai, questions, speech_goal, ...rest } = form;
    const questionList = questions.split("\n").map((q) => q.trim()).filter(Boolean);
    if (questionList.length > 20) {
      setError("Maximal 20 Leitfragen.");
      return;
    }
    const payload = {
      ...rest,
      ...aiPayload(ai),
      questions: questionList.length ? questionList : null,
      speech_goal: speech_goal.trim() || null,
    };
    try {
      if (editing) {
        await update.mutateAsync({ id: editing.id, data: payload });
      } else {
        await create.mutateAsync({ ...payload, lesson_id, task_kind: kind });
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
          {kind === "FRAGE" ? "Neue Frage des Themas" : "Neue Sprechübung"}
        </AdminButton>
      </div>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage={kind === "FRAGE" ? "Noch keine Frage des Themas angelegt." : "Noch keine Sprechübungen angelegt."}
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={kind === "FRAGE" ? (editing ? "Frage des Themas bearbeiten" : "Neue Frage des Themas") : editing ? "Sprechübung bearbeiten" : "Neue Sprechübung"}
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

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Form</label>
              <AdminSelect
                value={form.response_type}
                onChange={(e) => setForm({ ...form, response_type: e.target.value as "MONOLOG" | "DIALOG" })}
                aria-label="Form"
              >
                <option value="MONOLOG">Monolog</option>
                <option value="DIALOG">Dialog / Rollenspiel</option>
              </AdminSelect>
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Leitfragen (eine pro Zeile, optional)</label>
              <AdminTextarea
                rows={3}
                value={form.questions}
                onChange={(e) => setForm({ ...form, questions: e.target.value })}
                placeholder={"Wie heißen Sie?\nWoher kommen Sie?"}
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Sprechziel (nur für die KI-Bewertung, optional)
            </label>
            <AdminTextarea
              rows={2}
              value={form.speech_goal}
              onChange={(e) => setForm({ ...form, speech_goal: e.target.value })}
              placeholder="Name, Herkunft, Wohnort und ein Hobby nennen"
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

          <AiTaskFields value={form.ai} onChange={(ai) => setForm({ ...form, ai })} defaultRubric={levelDefault.rubric ?? DEFAULT_SPEAKING_RUBRIC} level={levelDefault.level} />

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
