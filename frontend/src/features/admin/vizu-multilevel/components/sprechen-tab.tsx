"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, Loader2, Mic, Pencil, Plus, Star, Trash2 } from "lucide-react";

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
const AUFGABEN = [1, 2, 3, 4, 5];
const QUERY_KEY = ["vizu-multilevel-admin-sprechen-content"];

interface FormState {
  title: string;
  level: string;
  order_index: number;
  instruction: string;
  preparation_text: string;
  prep_seconds: number;
  min_seconds: number;
  max_seconds: number;
  points: number;
  is_active: boolean;
}

function emptyForm(order: number, level: string): FormState {
  return {
    title: "",
    level,
    order_index: order,
    instruction: "",
    preparation_text: "",
    prep_seconds: 0,
    min_seconds: 30,
    max_seconds: 60,
    points: 20,
    is_active: true,
  };
}

function errorMessage(error: unknown): string {
  const data = (error as { response?: { data?: { message?: unknown } } }).response?.data;
  return typeof data?.message === "string" ? data.message : "Speichern fehlgeschlagen. Bitte Eingaben prüfen.";
}

/** Same rule as the backend (sprechen_service.assigned_tasks): Aufgabe n uses
 * the active variant at level LADDER[n-1], else the nearest active level. */
function usedVariant(variants: VizuMultilevelSpeakingTaskAdmin[], order: number): string | null {
  const active = variants.filter((v) => v.is_active);
  if (!active.length) return null;
  const target = order - 1;
  const rank = (l: string) => (LEVELS.indexOf(l) === -1 ? 99 : LEVELS.indexOf(l));
  return [...active].sort((a, b) => Math.abs(rank(a.level) - target) - Math.abs(rank(b.level) - target) || rank(a.level) - rank(b.level))[0].id;
}

/** Sprechen bank: 5 Aufgaben (task types) x internal CEFR level. Students get
 * Aufgabe 1 @ A1 … Aufgabe 5 @ C1; every other variant is spare content that
 * takes over if the admin deactivates the ladder variant. Answers are
 * transcribed and AI-evaluated automatically (teachers may override). */
export default function VizuMultilevelSprechenTab() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<VizuMultilevelSpeakingTaskAdmin | "new" | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm(1, "A1"));
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<VizuMultilevelSpeakingTaskAdmin | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data: tasks, isLoading } = useQuery({ queryKey: QUERY_KEY, queryFn: listVizuMultilevelSprechenTasks });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: QUERY_KEY });

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        ...form,
        title: form.title.trim(),
        instruction: form.instruction.trim(),
        preparation_text: form.preparation_text.trim() || null,
      };
      return editing === "new"
        ? createVizuMultilevelSprechenTask(payload)
        : updateVizuMultilevelSprechenTask((editing as VizuMultilevelSpeakingTaskAdmin).id, payload);
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
    onError: (e) => {
      setDeleteError(errorMessage(e));
      setDeleteTarget(null);
    },
  });

  function openNew(order = 1, level = "A1") {
    setError(null);
    setForm(emptyForm(order, level));
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
      min_seconds: task.min_seconds,
      max_seconds: task.max_seconds,
      points: task.points,
      is_active: task.is_active,
    });
    setEditing(task);
  }

  const num = (value: string) => {
    const n = Number.parseInt(value, 10);
    return Number.isNaN(n) ? 0 : n;
  };

  return (
    <div className="space-y-4">
      <AdminCard>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <p className="max-w-2xl text-sm text-[var(--admin-text-secondary)]">
            5 Sprechen-Aufgaben × 5 Niveaus. Studenten erhalten Aufgabe 1 (A1) bis Aufgabe 5 (C1) — markiert mit „Für Studenten“. Die
            Antworten werden automatisch transkribiert und von der KI bewertet (je 20 Punkte, gesamt 100). Das Niveau ist intern und für
            Studenten unsichtbar.
          </p>
          <AdminButton onClick={() => openNew()}>
            <Plus size={15} />
            Neue Variante
          </AdminButton>
        </div>
      </AdminCard>

      {deleteError && <p className="text-sm text-[var(--admin-danger)]">{deleteError}</p>}

      {isLoading && (
        <div className="flex h-40 items-center justify-center">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      )}

      {!isLoading && (!tasks || tasks.length === 0) && (
        <AdminEmptySection
          icon={Mic}
          title="Noch kein Sprechen-Inhalt vorhanden"
          description="Der Standard-Inhalt (25 Varianten) wird automatisch angelegt, sobald ein Student Sprechen öffnet — oder per Seed-Skript."
        />
      )}

      {tasks &&
        AUFGABEN.map((order) => {
          const variants = tasks.filter((t) => t.order_index === order);
          if (!variants.length) return null;
          const used = usedVariant(variants, order);
          return (
            <AdminCard key={order}>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-bold text-[var(--admin-text-primary)]">
                  Aufgabe {order} · {variants[0].title}
                </p>
                <span className="text-xs text-[var(--admin-text-muted)]">Ziel für Studenten: {LEVELS[order - 1]}</span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                {LEVELS.map((level) => {
                  const task = variants.find((v) => v.level === level);
                  if (!task) {
                    return (
                      <button
                        key={level}
                        type="button"
                        onClick={() => openNew(order, level)}
                        className="flex min-h-[120px] flex-col items-center justify-center rounded-xl border border-dashed border-[var(--admin-border)] text-xs text-[var(--admin-text-muted)] hover:border-[var(--admin-primary)]"
                      >
                        <Plus size={14} />
                        {level} anlegen
                      </button>
                    );
                  }
                  return (
                    <div
                      key={task.id}
                      className={`flex flex-col rounded-xl p-3 ring-1 ${task.id === used ? "ring-2 ring-orange-400" : "ring-[var(--admin-border)]"}`}
                    >
                      <div className="mb-1 flex items-center justify-between">
                        <span className="rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-xs font-bold text-[var(--admin-primary)]">{task.level}</span>
                        {task.id === used && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-orange-500">
                            <Star size={10} /> Für Studenten
                          </span>
                        )}
                      </div>
                      <p className="line-clamp-3 flex-1 text-xs text-[var(--admin-text-secondary)]">{task.instruction}</p>
                      <p className="mt-2 text-[10px] text-[var(--admin-text-muted)]">
                        {task.min_seconds}–{task.max_seconds} s · {task.points} P · {task.is_active ? "aktiv" : "inaktiv"}
                      </p>
                      <div className="mt-2 flex gap-1">
                        <AdminButton size="sm" variant="secondary" onClick={() => openEdit(task)} aria-label="Bearbeiten">
                          <Pencil size={12} />
                        </AdminButton>
                        <AdminButton
                          size="sm"
                          variant="secondary"
                          onClick={() => toggleMutation.mutate(task)}
                          disabled={toggleMutation.isPending}
                          aria-label={task.is_active ? "Deaktivieren" : "Aktivieren"}
                        >
                          {task.is_active ? <EyeOff size={12} /> : <Eye size={12} />}
                        </AdminButton>
                        <AdminButton
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setDeleteError(null);
                            setDeleteTarget(task);
                          }}
                          aria-label="Löschen"
                        >
                          <Trash2 size={12} />
                        </AdminButton>
                      </div>
                    </div>
                  );
                })}
              </div>
            </AdminCard>
          );
        })}

      <FormDialog
        open={editing !== null}
        onOpenChange={(open) => !open && setEditing(null)}
        title={editing === "new" ? "Neue Sprechen-Variante" : "Sprechen-Variante bearbeiten"}
        size="xl"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setEditing(null)} disabled={saveMutation.isPending}>
              Abbrechen
            </AdminButton>
            <AdminButton onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending || !form.title.trim() || !form.instruction.trim()}>
              {saveMutation.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-[1fr_140px_140px]">
            <div>
              <AdminLabel>Titel (Aufgabentyp)</AdminLabel>
              <AdminInput value={form.title} maxLength={255} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </div>
            <div>
              <AdminLabel>Aufgabe</AdminLabel>
              <AdminSelect value={form.order_index} onChange={(e) => setForm({ ...form, order_index: num(e.target.value) })}>
                {AUFGABEN.map((n) => (
                  <option key={n} value={n}>
                    Aufgabe {n}
                  </option>
                ))}
              </AdminSelect>
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
            <AdminLabel>Anleitung</AdminLabel>
            <AdminTextarea value={form.instruction} onChange={(e) => setForm({ ...form, instruction: e.target.value })} rows={4} />
          </div>

          <div>
            <AdminLabel>Hinweise zur Vorbereitung (optional)</AdminLabel>
            <AdminTextarea value={form.preparation_text} onChange={(e) => setForm({ ...form, preparation_text: e.target.value })} rows={2} />
          </div>

          <div className="grid gap-4 sm:grid-cols-4">
            <div>
              <AdminLabel>Min. Sprechzeit (Sek.)</AdminLabel>
              <AdminInput type="number" min={0} step={1} value={form.min_seconds} onChange={(e) => setForm({ ...form, min_seconds: num(e.target.value) })} />
            </div>
            <div>
              <AdminLabel>Max. Sprechzeit (Sek.)</AdminLabel>
              <AdminInput type="number" min={10} step={1} value={form.max_seconds} onChange={(e) => setForm({ ...form, max_seconds: num(e.target.value) })} />
            </div>
            <div>
              <AdminLabel>Vorbereitung (Sek.)</AdminLabel>
              <AdminInput type="number" min={0} step={1} value={form.prep_seconds} onChange={(e) => setForm({ ...form, prep_seconds: num(e.target.value) })} />
            </div>
            <div>
              <AdminLabel>Punkte</AdminLabel>
              <AdminInput type="number" min={1} step={1} value={form.points} onChange={(e) => setForm({ ...form, points: num(e.target.value) })} />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <AdminCheckbox checked={form.is_active} onCheckedChange={(checked) => setForm({ ...form, is_active: checked })} aria-label="Aktiv" />
            <span className="text-sm text-[var(--admin-text-primary)]">Aktiv</span>
          </div>

          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
        </div>
      </FormDialog>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(o) => !o && setDeleteTarget(null)}
        title="Variante löschen"
        description={deleteTarget ? `Aufgabe ${deleteTarget.order_index} (${deleteTarget.level}) wirklich löschen? Bereits beantwortete Aufgaben können nur deaktiviert werden.` : ""}
        onConfirm={() => deleteMutation.mutate()}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
