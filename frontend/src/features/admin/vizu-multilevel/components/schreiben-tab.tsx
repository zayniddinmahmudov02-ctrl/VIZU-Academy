"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, Loader2, PenLine, Pencil, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FileUploadField from "@/components/admin/file-upload-field";
import FormDialog from "@/components/admin/form-dialog";
import {
  createVizuMultilevelSchreibenTask,
  deleteVizuMultilevelSchreibenTask,
  listVizuMultilevelSchreibenTasks,
  updateVizuMultilevelSchreibenTask,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type { VizuMultilevelWritingTaskAdmin } from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";
import RubricCriteriaEditor from "./rubric-criteria-editor";

const LEVELS = ["A1", "A2", "B1", "B2", "C1"];

interface FormState {
  title: string;
  level: string;
  order_index: number;
  instruction: string;
  min_words: number;
  max_words: number;
  image_url: string | null;
  points: number;
  is_active: boolean;
  rubric_criteria: VizuMultilevelWritingTaskAdmin["rubric_criteria"];
}

function toFormState(task: VizuMultilevelWritingTaskAdmin): FormState {
  return {
    title: task.title,
    level: task.level,
    order_index: task.order_index,
    instruction: task.instruction,
    min_words: task.min_words,
    max_words: task.max_words,
    image_url: task.image_url,
    points: task.points,
    is_active: task.is_active,
    rubric_criteria: task.rubric_criteria,
  };
}

function emptyForm(order: number): FormState {
  return {
    title: "",
    level: "A1",
    order_index: order,
    instruction: "",
    min_words: 30,
    max_words: 120,
    image_url: null,
    points: 20,
    is_active: true,
    rubric_criteria: [],
  };
}

function errorMessage(error: unknown): string {
  const data = (error as { response?: { data?: { message?: unknown } } }).response?.data;
  return typeof data?.message === "string" ? data.message : "Speichern fehlgeschlagen. Bitte Eingaben prüfen.";
}

export default function VizuMultilevelSchreibenTab() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<VizuMultilevelWritingTaskAdmin | "new" | null>(null);
  const [form, setForm] = useState<FormState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<VizuMultilevelWritingTaskAdmin | null>(null);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-multilevel-admin-schreiben-content"],
    queryFn: listVizuMultilevelSchreibenTasks,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-admin-schreiben-content"] });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (editing === "new") {
        // A new Aufgabe needs a rubric for the teacher to grade against; if
        // none was entered, default to one criterion worth the full points.
        const rubric =
          form!.rubric_criteria.length > 0
            ? form!.rubric_criteria
            : [{ id: null, name: "Gesamtbewertung", max_score: form!.points, order_index: 1 }];
        return createVizuMultilevelSchreibenTask({ ...form!, rubric_criteria: rubric });
      }
      return updateVizuMultilevelSchreibenTask((editing as VizuMultilevelWritingTaskAdmin).id, form!);
    },
    onSuccess: () => {
      invalidate();
      setEditing(null);
      setForm(null);
    },
    onError: (e) => setError(errorMessage(e)),
  });

  const toggleMutation = useMutation({
    mutationFn: (task: VizuMultilevelWritingTaskAdmin) => updateVizuMultilevelSchreibenTask(task.id, { is_active: !task.is_active }),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteVizuMultilevelSchreibenTask(deleteTarget!.id),
    onSuccess: () => {
      invalidate();
      setDeleteTarget(null);
    },
  });

  function openNew() {
    setError(null);
    setForm(emptyForm((tasks?.reduce((max, t) => Math.max(max, t.order_index), 0) ?? 0) + 1));
    setEditing("new");
  }

  function openEdit(task: VizuMultilevelWritingTaskAdmin) {
    setError(null);
    setEditing(task);
    setForm(toFormState(task));
  }

  function closeDialog() {
    setEditing(null);
    setForm(null);
  }

  if (isLoading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
      </div>
    );
  }

  return (
    <div>
      <AdminCard className="mb-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <p className="max-w-xl text-sm text-[var(--admin-text-secondary)]">
            Schreiben-Aufgaben: Thema, Anleitung, Wortanzahl, Bild, Punkte, Bewertungsraster (Rubric) und Status. Eine
            Lehrkraft bewertet die Texte im Teacher Panel. Das Niveau ist rein intern.
          </p>
          <AdminButton onClick={openNew}>
            <Plus size={15} />
            Neue Aufgabe
          </AdminButton>
        </div>
      </AdminCard>

      {(!tasks || tasks.length === 0) && (
        <AdminEmptySection
          icon={PenLine}
          title="Noch kein Schreiben-Inhalt vorhanden"
          description="Der Inhalt ist bewusst leer. Lege oben die erste Schreiben-Aufgabe an."
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tasks?.map((task) => {
          const rubricTotal = task.rubric_criteria.reduce((sum, c) => sum + c.max_score, 0);
          return (
            <AdminCard key={task.id}>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Aufgabe {task.order_index}</p>
                <span className="rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-primary)]">
                  {task.level}
                </span>
              </div>
              <p className="mb-1 truncate text-sm font-medium text-[var(--admin-text-primary)]">{task.title}</p>
              <p className="mb-3 text-xs text-[var(--admin-text-muted)]">
                {task.min_words}–{task.max_words} Wörter · {task.points} Punkte · Rubric {rubricTotal}/20
              </p>
              <div className="mb-3 flex items-center gap-2">
                <span
                  className={
                    task.is_active
                      ? "rounded-full bg-[var(--admin-success,#22c55e)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-success,#22c55e)]"
                      : "rounded-full bg-[var(--admin-text-muted)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-text-muted)]"
                  }
                >
                  {task.is_active ? "Veröffentlicht" : "Entwurf"}
                </span>
                {task.image_url && (
                  <span className="rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-primary)]">
                    Bild vorhanden
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-1.5">
                <AdminButton variant="secondary" size="sm" onClick={() => toggleMutation.mutate(task)} disabled={toggleMutation.isPending}>
                  {task.is_active ? <EyeOff size={13} /> : <Eye size={13} />}
                  {task.is_active ? "Zurückziehen" : "Veröffentlichen"}
                </AdminButton>
                <AdminButton variant="secondary" size="sm" onClick={() => openEdit(task)}>
                  <Pencil size={13} />
                  Bearbeiten
                </AdminButton>
                <AdminButton variant="ghost" size="sm" onClick={() => setDeleteTarget(task)}>
                  <Trash2 size={13} />
                </AdminButton>
              </div>
            </AdminCard>
          );
        })}
      </div>

      <FormDialog
        open={!!editing}
        onOpenChange={(open) => !open && closeDialog()}
        title={editing === "new" ? "Neue Schreiben-Aufgabe" : editing ? `Aufgabe ${editing.order_index} bearbeiten` : ""}
        size="xl"
        footer={
          form && (
            <>
              <AdminButton variant="ghost" onClick={closeDialog} disabled={updateMutation.isPending}>
                Abbrechen
              </AdminButton>
              <AdminButton onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending || !form.title.trim()}>
                {updateMutation.isPending ? "Wird gespeichert..." : "Speichern"}
              </AdminButton>
            </>
          )
        }
      >
        {form && (
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-[1fr_120px]">
              <div>
                <AdminLabel>Titel</AdminLabel>
                <AdminInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              </div>
              <div>
                <AdminLabel>Niveau (intern)</AdminLabel>
                <AdminSelect value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}>
                  {LEVELS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </AdminSelect>
              </div>
            </div>

            <div>
              <AdminLabel>Reihenfolge</AdminLabel>
              <AdminInput
                type="number"
                min={1}
                value={form.order_index}
                onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })}
              />
            </div>

            <div>
              <AdminLabel>Anleitung</AdminLabel>
              <AdminTextarea
                value={form.instruction}
                onChange={(e) => setForm({ ...form, instruction: e.target.value })}
                rows={8}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <AdminLabel>Minimum Wörter</AdminLabel>
                <AdminInput
                  type="number"
                  min={0}
                  value={form.min_words}
                  onChange={(e) => setForm({ ...form, min_words: Number(e.target.value) })}
                />
              </div>
              <div>
                <AdminLabel>Maximum Wörter</AdminLabel>
                <AdminInput
                  type="number"
                  min={0}
                  value={form.max_words}
                  onChange={(e) => setForm({ ...form, max_words: Number(e.target.value) })}
                />
              </div>
              <div>
                <AdminLabel>Punkte</AdminLabel>
                <AdminInput
                  type="number"
                  min={0}
                  value={form.points}
                  onChange={(e) => setForm({ ...form, points: Number(e.target.value) })}
                />
              </div>
            </div>

            <FileUploadField
              label="Bild (optional)"
              value={form.image_url}
              onChange={(url) => setForm({ ...form, image_url: url })}
              folder="images"
              accept="image/*"
            />

            <div>
              <AdminLabel>Rubric</AdminLabel>
              <RubricCriteriaEditor
                criteria={form.rubric_criteria}
                onChange={(rubric_criteria) => setForm({ ...form, rubric_criteria })}
              />
            </div>

            <div className="flex items-center gap-2">
              <AdminCheckbox
                checked={form.is_active}
                onCheckedChange={(checked) => setForm({ ...form, is_active: checked })}
                aria-label="Aktiv"
              />
              <span className="text-sm text-[var(--admin-text-primary)]">Veröffentlicht (für Studenten sichtbar)</span>
            </div>
            {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
          </div>
        )}
      </FormDialog>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(o) => !o && setDeleteTarget(null)}
        title="Aufgabe löschen"
        description={deleteTarget ? `Schreiben-Aufgabe ${deleteTarget.order_index} wirklich löschen?` : ""}
        onConfirm={() => deleteMutation.mutate()}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
