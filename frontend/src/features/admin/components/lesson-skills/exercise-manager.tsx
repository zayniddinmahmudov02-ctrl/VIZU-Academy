"use client";

import { useState } from "react";
import { Copy, Eye, EyeOff, ListChecks, Pencil, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  apiErrorMessage,
  createExercise,
  deleteExercise,
  duplicateItem,
  updateExercise,
  type AdminExercise,
  type ExerciseSkill,
} from "@/features/admin/services/lesson-skills-admin-service";

import QuestionEditorDialog from "./question-editor-dialog";
import { ItemCard, PublishBadge, useLessonSkillsOverview } from "./shared";

const EMPTY = { title: "", instruction: "", order_index: 1, source: "book" as "book" | "vizu" };

const KEY_ERRORS: Record<string, string> = {
  NO_QUESTIONS: "Ohne Fragen kann die Übung nicht veröffentlicht werden.",
  KEY_REQUIRED: "Jede Frage braucht zuerst eine Lösung.",
};

/** Auto-graded exercise sets of one skill (Grammatik / Wortschatz practice,
 * Yakuniy Test): create, edit questions + answer key, publish / hide,
 * duplicate, delete. Students get them without the key; grading is on the
 * server. */
export default function ExerciseManager({ lessonId, skill, label }: { lessonId: string; skill: ExerciseSkill; label: string }) {
  const { data, isLoading, refresh } = useLessonSkillsOverview(lessonId);
  const sets = (data?.exercises ?? []).filter((e) => e.skill === skill);

  const [editing, setEditing] = useState<AdminExercise | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [questionsFor, setQuestionsFor] = useState<AdminExercise | null>(null);
  const [deleting, setDeleting] = useState<AdminExercise | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(action: () => Promise<unknown>, fallback = "Aktion fehlgeschlagen.") {
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh();
      return true;
    } catch (err) {
      const msg = apiErrorMessage(err, fallback);
      setError(KEY_ERRORS[msg] ?? msg);
      return false;
    } finally {
      setBusy(false);
    }
  }

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY, order_index: sets.length + 1 });
    setError(null);
    setFormOpen(true);
  }

  function openEdit(item: AdminExercise) {
    setEditing(item);
    setForm({ title: item.title, instruction: item.instruction ?? "", order_index: item.order_index, source: item.source });
    setError(null);
    setFormOpen(true);
  }

  async function save() {
    const payload = { title: form.title.trim(), instruction: form.instruction.trim() || null, order_index: form.order_index, source: form.source };
    const ok = await run(
      () => (editing ? updateExercise(editing.id, payload) : createExercise(lessonId, { ...payload, skill, is_published: false })),
      "Speichern fehlgeschlagen.",
    );
    if (ok) setFormOpen(false);
  }

  const published = sets.filter((s) => s.is_published);

  return (
    <div className="space-y-4" data-testid={`admin-exercises-${skill.toLowerCase()}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[var(--admin-text-secondary)]">
          {label}: {sets.length} Übungen · {sets.reduce((n, s) => n + s.question_count, 0)} Fragen · für Schüler sichtbar: {published.length}
        </p>
        <AdminButton onClick={openCreate} data-testid={`exercise-new-${skill.toLowerCase()}`}>
          <Plus size={16} /> Neue Übung
        </AdminButton>
      </div>

      {error && !formOpen && <p className="text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {!isLoading && sets.length === 0 && (
        <p className="rounded-2xl bg-[var(--admin-card)] p-6 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
          Noch keine Übungen.
        </p>
      )}

      {sets.map((item) => (
        <ItemCard
          key={item.id}
          testId="exercise-item"
          title={`${item.order_index}. ${item.title}`}
          badge={
            <span className="flex flex-wrap gap-1.5">
              <PublishBadge published={item.is_published} />
              <span className="rounded-full bg-white/5 px-2.5 py-1 text-xs font-semibold text-[var(--admin-text-muted)]">
                {item.source === "book" ? "Buch" : "VIZU"}
              </span>
            </span>
          }
          meta={`${item.question_count} Fragen · ${item.max_points} Punkte${item.content_id ? ` · ${item.content_id}` : ""}`}
          actions={
            <>
              <AdminButton size="sm" variant="secondary" onClick={() => setQuestionsFor(item)} data-testid="exercise-questions">
                <ListChecks size={14} /> Fragen
              </AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={() => openEdit(item)} aria-label="Bearbeiten">
                <Pencil size={14} />
              </AdminButton>
              <AdminButton
                size="sm"
                variant="ghost"
                disabled={busy}
                onClick={() => run(() => updateExercise(item.id, { is_published: !item.is_published }))}
                aria-label={item.is_published ? "Verbergen" : "Veröffentlichen"}
                title={item.is_published ? "Verbergen" : "Veröffentlichen"}
                data-testid="exercise-toggle-publish"
              >
                {item.is_published ? <EyeOff size={14} /> : <Eye size={14} />}
              </AdminButton>
              <AdminButton size="sm" variant="ghost" disabled={busy} onClick={() => run(() => duplicateItem("exercises", item.id))} aria-label="Duplizieren" title="Duplizieren">
                <Copy size={14} />
              </AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={() => setDeleting(item)} aria-label="Löschen">
                <Trash2 size={14} />
              </AdminButton>
            </>
          }
        >
          {item.instruction && <p className="line-clamp-2 text-sm text-[var(--admin-text-secondary)]">{item.instruction}</p>}
        </ItemCard>
      ))}

      <FormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        title={editing ? "Übung bearbeiten" : "Neue Übung"}
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setFormOpen(false)}>Abbrechen</AdminButton>
            <AdminButton onClick={save} disabled={busy || !form.title.trim()} data-testid="exercise-save">
              {busy ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Titel</label>
            <AdminInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Test: Possessivpronomen (20)" />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Anweisung (optional)</label>
            <AdminTextarea rows={3} value={form.instruction} onChange={(e) => setForm({ ...form, instruction: e.target.value })} />
          </div>
          <div className="flex flex-wrap items-end gap-6">
            <div className="w-32">
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Reihenfolge</label>
              <AdminInput type="number" min={1} value={form.order_index} onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })} />
            </div>
            <div className="w-56">
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Quelle</label>
              <AdminSelect value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value as "book" | "vizu" })} aria-label="Quelle">
                <option value="book">Aus dem Buch</option>
                <option value="vizu">Von VIZU erstellt</option>
              </AdminSelect>
            </div>
          </div>
          {!editing && <p className="text-xs text-[var(--admin-text-muted)]">Die Übung wird verborgen angelegt. Fragen hinzufügen, dann veröffentlichen.</p>}
        </div>
      </FormDialog>

      {questionsFor && (
        <QuestionEditorDialog
          key={questionsFor.id}
          open
          onOpenChange={(open) => !open && setQuestionsFor(null)}
          kind="exercises"
          ownerId={questionsFor.id}
          title={questionsFor.title}
          initial={questionsFor.questions}
          onSaved={refresh}
        />
      )}

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Übung löschen"
        description={`"${deleting?.title}" und ihre Fragen werden gelöscht, auch die Versuche der Schüler dazu.`}
        isPending={busy}
        onConfirm={async () => {
          if (!deleting) return;
          if (await run(() => deleteExercise(deleting.id), "Löschen fehlgeschlagen.")) setDeleting(null);
        }}
      />
    </div>
  );
}
