"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, Loader2, Mic, Pencil, Plus, Trash2 } from "lucide-react";

import {
  AdminButton,
  AdminCard,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
  AdminSelect,
  AdminTextarea,
} from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  createVizuMultilevelSprechenTask,
  deleteVizuMultilevelSprechenTask,
  listVizuMultilevelSprechenTasks,
  updateVizuMultilevelSprechenTask,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type { VizuMultilevelSpeakingTaskAdmin } from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";

const LEVELS = ["A1", "A2", "B1", "B2", "C1"];
const QUERY_KEY = ["vizu-multilevel-admin-sprechen-content"];

interface FormState {
  title: string;
  level: string;
  order_index: number;
  instruction: string;
  preparation_text: string;
  prep_seconds: number;
  max_seconds: number;
  points: number;
  is_active: boolean;
}

function emptyForm(order: number): FormState {
  return {
    title: "",
    level: "A1",
    order_index: order,
    instruction: "",
    preparation_text: "",
    prep_seconds: 0,
    max_seconds: 120,
    points: 20,
    is_active: true,
  };
}

function errorMessage(error: unknown): string {
  const data = (error as { response?: { data?: { message?: unknown } } }).response?.data;
  return typeof data?.message === "string" ? data.message : "Speichern fehlgeschlagen. Bitte Eingaben prüfen.";
}

export default function VizuMultilevelSprechenTab() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<VizuMultilevelSpeakingTaskAdmin | "new" | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm(1));
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<VizuMultilevelSpeakingTaskAdmin | null>(null);

  const { data: tasks, isLoading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: listVizuMultilevelSprechenTasks,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: QUERY_KEY });

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = { ...form, preparation_text: form.preparation_text || null };
      return editing === "new" ? createVizuMultilevelSprechenTask(payload) : updateVizuMultilevelSprechenTask((editing as VizuMultilevelSpeakingTaskAdmin).id, payload);
    },
    onSuccess: () => {
      invalidate();
      setEditing(null);
    },
    onError: (e) => setError(errorMessage(e)),
  });

  const toggleMutation = useMutation({
    mutationFn: (task: VizuMultilevelSpeakingTaskAdmin) => updateVizuMultilevelSprechenTask(task.id, { is_active: !task.is_active }),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteVizuMultilevelSprechenTask(deleteTarget!.id),
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

  function openEdit(task: VizuMultilevelSpeakingTaskAdmin) {
    setError(null);
    setForm({
      title: task.title,
      level: task.level,
      order_index: task.order_index,
      instruction: task.instruction,
      preparation_text: task.preparation_text ?? "",
      prep_seconds: task.prep_seconds,
      max_seconds: task.max_seconds,
      points: task.points,
      is_active: task.is_active,
    });
    setEditing(task);
  }

  return (
    <div className="space-y-4">
      <AdminCard>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <p className="max-w-xl text-sm text-[var(--admin-text-secondary)]">
            Sprechen-Aufgaben: Thema, Anleitung, optionale Vorbereitung und Aufnahmedauer. Studenten nehmen ihre Antwort auf, eine
            Lehrkraft bewertet sie im Teacher Panel. Das Niveau ist rein intern.
          </p>
          <AdminButton onClick={openNew}>
            <Plus size={15} />
            Neue Aufgabe
          </AdminButton>
        </div>
      </AdminCard>

      {isLoading && (
        <div className="flex h-40 items-center justify-center">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      )}

      {!isLoading && (!tasks || tasks.length === 0) && (
        <AdminEmptySection
          icon={Mic}
          title="Noch kein Sprechen-Inhalt vorhanden"
          description="Der Inhalt ist bewusst leer. Lege oben die erste Sprechen-Aufgabe an."
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tasks?.map((task) => (
          <AdminCard key={task.id}>
            <div className="mb-2 flex items-center justify-between">
              <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Aufgabe {task.order_index}</p>
              <span className="rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-primary)]">
                {task.level}
              </span>
            </div>
            <p className="mb-1 truncate text-sm font-medium text-[var(--admin-text-primary)]">{task.title}</p>
            <p className="mb-3 text-xs text-[var(--admin-text-muted)]">
              max. {task.max_seconds}s · {task.points} Punkte
              {task.prep_seconds > 0 ? ` · Vorbereitung ${task.prep_seconds}s` : ""}
            </p>
            <span
              className={
                task.is_active
                  ? "rounded-full bg-[var(--admin-success,#22c55e)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-success,#22c55e)]"
                  : "rounded-full bg-[var(--admin-text-muted)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-text-muted)]"
              }
            >
              {task.is_active ? "Veröffentlicht" : "Entwurf"}
            </span>
            <div className="mt-3 flex flex-wrap gap-1.5">
              <AdminButton size="sm" variant="secondary" onClick={() => toggleMutation.mutate(task)} disabled={toggleMutation.isPending}>
                {task.is_active ? <EyeOff size={13} /> : <Eye size={13} />}
                {task.is_active ? "Zurückziehen" : "Veröffentlichen"}
              </AdminButton>
              <AdminButton size="sm" variant="secondary" onClick={() => openEdit(task)}>
                <Pencil size={13} />
                Bearbeiten
              </AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={() => setDeleteTarget(task)}>
                <Trash2 size={13} />
              </AdminButton>
            </div>
          </AdminCard>
        ))}
      </div>

      <FormDialog
        open={editing !== null}
        onOpenChange={(open) => !open && setEditing(null)}
        title={editing === "new" ? "Neue Sprechen-Aufgabe" : "Sprechen-Aufgabe bearbeiten"}
        size="xl"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setEditing(null)} disabled={saveMutation.isPending}>
              Abbrechen
            </AdminButton>
            <AdminButton onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
              {saveMutation.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-[1fr_120px_120px]">
            <div>
              <AdminLabel>Thema</AdminLabel>
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
            <div>
              <AdminLabel>Reihenfolge</AdminLabel>
              <AdminInput
                type="number"
                min={1}
                value={form.order_index}
                onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })}
              />
            </div>
          </div>

          <div>
            <AdminLabel>Anleitung</AdminLabel>
            <AdminTextarea value={form.instruction} onChange={(e) => setForm({ ...form, instruction: e.target.value })} rows={5} />
          </div>

          <div>
            <AdminLabel>Hinweise zur Vorbereitung (optional)</AdminLabel>
            <AdminTextarea
              value={form.preparation_text}
              onChange={(e) => setForm({ ...form, preparation_text: e.target.value })}
              rows={3}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <AdminLabel>Vorbereitungszeit (Sek.)</AdminLabel>
              <AdminInput
                type="number"
                min={0}
                value={form.prep_seconds}
                onChange={(e) => setForm({ ...form, prep_seconds: Number(e.target.value) })}
              />
            </div>
            <div>
              <AdminLabel>Max. Aufnahmedauer (Sek.)</AdminLabel>
              <AdminInput
                type="number"
                min={10}
                value={form.max_seconds}
                onChange={(e) => setForm({ ...form, max_seconds: Number(e.target.value) })}
              />
            </div>
            <div>
              <AdminLabel>Punkte</AdminLabel>
              <AdminInput
                type="number"
                min={1}
                value={form.points}
                onChange={(e) => setForm({ ...form, points: Number(e.target.value) })}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <AdminCheckbox
              checked={form.is_active}
              onCheckedChange={(checked) => setForm({ ...form, is_active: checked })}
              aria-label="Veröffentlicht"
            />
            <span className="text-sm text-[var(--admin-text-primary)]">Veröffentlicht (für Studenten sichtbar)</span>
          </div>

          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
        </div>
      </FormDialog>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(o) => !o && setDeleteTarget(null)}
        title="Aufgabe löschen"
        description={deleteTarget ? `Sprechen-Aufgabe ${deleteTarget.order_index} wirklich löschen?` : ""}
        onConfirm={() => deleteMutation.mutate()}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
