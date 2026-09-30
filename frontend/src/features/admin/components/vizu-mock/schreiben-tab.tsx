"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Pencil } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import FileUploadField from "@/components/admin/file-upload-field";
import FormDialog from "@/components/admin/form-dialog";
import {
  listVizuMockSchreibenTasks,
  updateVizuMockSchreibenTask,
} from "@/features/admin/services/vizu-mock-admin-service";
import type { VizuMockWritingTaskAdmin } from "@/features/admin/types/vizu-mock-admin.types";
import RubricCriteriaEditor from "./rubric-criteria-editor";

const LEVELS = ["A1", "A2", "B1", "B2", "C1"];

interface FormState {
  title: string;
  level: string;
  instruction: string;
  min_words: number;
  max_words: number;
  image_url: string | null;
  points: number;
  is_active: boolean;
  rubric_criteria: VizuMockWritingTaskAdmin["rubric_criteria"];
}

function toFormState(task: VizuMockWritingTaskAdmin): FormState {
  return {
    title: task.title,
    level: task.level,
    instruction: task.instruction,
    min_words: task.min_words,
    max_words: task.max_words,
    image_url: task.image_url,
    points: task.points,
    is_active: task.is_active,
    rubric_criteria: task.rubric_criteria,
  };
}

export default function VizuMockSchreibenTab() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<VizuMockWritingTaskAdmin | null>(null);
  const [form, setForm] = useState<FormState | null>(null);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-mock-admin-schreiben-content"],
    queryFn: listVizuMockSchreibenTasks,
  });

  const updateMutation = useMutation({
    mutationFn: () => updateVizuMockSchreibenTask(editing!.id, form!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-schreiben-content"] });
      setEditing(null);
      setForm(null);
    },
  });

  function openEdit(task: VizuMockWritingTaskAdmin) {
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
      <p className="mb-4 text-sm text-[var(--admin-text-secondary)]">
        5 Schreiben-Aufgaben (je 20 Punkte, 100 insgesamt). Inhalte wurden importiert und können hier bearbeitet
        werden — Titel, Anleitung, Wortlimits, Bild, Punkte, Rubric und Status.
      </p>

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
                  {task.is_active ? "Aktiv" : "Inaktiv"}
                </span>
                {task.image_url && (
                  <span className="rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-primary)]">
                    Bild vorhanden
                  </span>
                )}
              </div>
              <AdminButton variant="secondary" size="sm" onClick={() => openEdit(task)}>
                <Pencil size={13} />
                Bearbeiten
              </AdminButton>
            </AdminCard>
          );
        })}
      </div>

      <FormDialog
        open={!!editing}
        onOpenChange={(open) => !open && closeDialog()}
        title={editing ? `Aufgabe ${editing.order_index} bearbeiten` : ""}
        size="xl"
        footer={
          form && (
            <>
              <AdminButton variant="ghost" onClick={closeDialog} disabled={updateMutation.isPending}>
                Abbrechen
              </AdminButton>
              <AdminButton onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending}>
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
                <AdminLabel>Niveau</AdminLabel>
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
              <span className="text-sm text-[var(--admin-text-primary)]">Aktiv (für Studenten sichtbar)</span>
            </div>
          </div>
        )}
      </FormDialog>
    </div>
  );
}
