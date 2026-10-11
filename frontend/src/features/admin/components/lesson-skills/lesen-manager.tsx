"use client";

import { useState } from "react";
import { Copy, Eye, EyeOff, ListChecks, Pencil, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import { apiErrorMessage, duplicateItem, type AdminLesenText } from "@/features/admin/services/lesson-skills-admin-service";
import { readingApi } from "@/features/admin/services/reading-service";

import QuestionEditorDialog from "./question-editor-dialog";
import { htmlToText, ItemCard, PublishBadge, textToHtml, useLessonSkillsOverview } from "./shared";

const EMPTY = { title: "", text: "", order_index: 1, is_published: false };

/** Lesen: the lesson's texts (Lesetexte) with their auto-graded questions.
 * Students see every published text with its questions as one test. */
export default function LesenManager({ lessonId }: { lessonId: string }) {
  const { data, isLoading, refresh } = useLessonSkillsOverview(lessonId);
  const texts = data?.lesen ?? [];

  const [editing, setEditing] = useState<AdminLesenText | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [questionsFor, setQuestionsFor] = useState<AdminLesenText | null>(null);
  const [deleting, setDeleting] = useState<AdminLesenText | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY, order_index: texts.length + 1 });
    setError(null);
    setFormOpen(true);
  }

  function openEdit(item: AdminLesenText) {
    setEditing(item);
    setForm({ title: item.title, text: htmlToText(item.content), order_index: item.order_index, is_published: item.is_published });
    setError(null);
    setFormOpen(true);
  }

  async function run(action: () => Promise<unknown>, fallback = "Aktion fehlgeschlagen.") {
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh();
      return true;
    } catch (err) {
      setError(apiErrorMessage(err, fallback));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    const payload = { title: form.title.trim(), content: textToHtml(form.text), order_index: form.order_index, is_published: form.is_published };
    const ok = await run(
      () => (editing ? readingApi.update(editing.id, payload) : readingApi.create({ ...payload, lesson_id: lessonId })),
      "Speichern fehlgeschlagen.",
    );
    if (ok) setFormOpen(false);
  }

  const totalQuestions = texts.reduce((n, t) => n + t.questions.length, 0);
  const published = texts.filter((t) => t.is_published);

  return (
    <div className="space-y-4" data-testid="admin-lesen">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[var(--admin-text-secondary)]">
          {texts.length} Texte · {totalQuestions} Fragen · für Schüler sichtbar: {published.length} Texte /{" "}
          {published.reduce((n, t) => n + t.questions.length, 0)} Fragen
        </p>
        <AdminButton onClick={openCreate} data-testid="lesen-new">
          <Plus size={16} /> Neuer Lesetext
        </AdminButton>
      </div>

      {error && !formOpen && <p className="text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {!isLoading && texts.length === 0 && (
        <p className="rounded-2xl bg-[var(--admin-card)] p-6 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
          Noch keine Lesetexte in dieser Lektion.
        </p>
      )}

      {texts.map((item) => (
        <ItemCard
          key={item.id}
          testId="lesen-item"
          title={`${item.order_index}. ${item.title}`}
          badge={<PublishBadge published={item.is_published} />}
          meta={`${item.questions.length} Fragen · ${item.questions.reduce((n, q) => n + q.points, 0)} Punkte`}
          actions={
            <>
              <AdminButton size="sm" variant="secondary" onClick={() => setQuestionsFor(item)} data-testid="lesen-questions">
                <ListChecks size={14} /> Fragen
              </AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={() => openEdit(item)} aria-label="Bearbeiten">
                <Pencil size={14} />
              </AdminButton>
              <AdminButton
                size="sm"
                variant="ghost"
                disabled={busy}
                onClick={() => run(() => readingApi.update(item.id, { is_published: !item.is_published }))}
                aria-label={item.is_published ? "Verbergen" : "Veröffentlichen"}
                title={item.is_published ? "Verbergen" : "Veröffentlichen"}
                data-testid="lesen-toggle-publish"
              >
                {item.is_published ? <EyeOff size={14} /> : <Eye size={14} />}
              </AdminButton>
              <AdminButton size="sm" variant="ghost" disabled={busy} onClick={() => run(() => duplicateItem("readings", item.id))} aria-label="Duplizieren" title="Duplizieren">
                <Copy size={14} />
              </AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={() => setDeleting(item)} aria-label="Löschen">
                <Trash2 size={14} />
              </AdminButton>
            </>
          }
        >
          <p className="line-clamp-3 text-sm text-[var(--admin-text-secondary)]">{htmlToText(item.content)}</p>
        </ItemCard>
      ))}

      <FormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        title={editing ? "Lesetext bearbeiten" : "Neuer Lesetext"}
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setFormOpen(false)}>Abbrechen</AdminButton>
            <AdminButton onClick={save} disabled={busy || !form.title.trim() || !form.text.trim()} data-testid="lesen-save">
              {busy ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Titel</label>
            <AdminInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Text 1: Tom" />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Text (Leerzeile = neuer Absatz)</label>
            <AdminTextarea rows={10} value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} />
          </div>
          <div className="flex flex-wrap items-end gap-6">
            <div className="w-32">
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Reihenfolge</label>
              <AdminInput type="number" min={1} value={form.order_index} onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })} />
            </div>
            <label className="flex cursor-pointer items-center gap-2.5 pb-2">
              <AdminCheckbox checked={form.is_published} onCheckedChange={(checked) => setForm({ ...form, is_published: checked })} />
              <span className="text-sm text-[var(--admin-text-secondary)]">Veröffentlicht</span>
            </label>
          </div>
        </div>
      </FormDialog>

      {questionsFor && (
        <QuestionEditorDialog
          key={questionsFor.id}
          open
          onOpenChange={(open) => !open && setQuestionsFor(null)}
          kind="readings"
          ownerId={questionsFor.id}
          title={questionsFor.title}
          initial={questionsFor.questions}
          onSaved={refresh}
        />
      )}

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Lesetext löschen"
        description={`"${deleting?.title}" und seine Fragen werden gelöscht. Bisherige Ergebnisse der Schüler bleiben gespeichert.`}
        isPending={busy}
        onConfirm={async () => {
          if (!deleting) return;
          if (await run(() => readingApi.remove(deleting.id), "Löschen fehlgeschlagen.")) setDeleting(null);
        }}
      />
    </div>
  );
}
