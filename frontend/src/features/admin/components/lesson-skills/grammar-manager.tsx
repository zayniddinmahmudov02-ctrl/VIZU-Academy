"use client";

import { useState } from "react";
import { Eye, EyeOff, Pencil, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import { apiErrorMessage, deleteGrammar, saveGrammar, type AdminGrammar } from "@/features/admin/services/lesson-skills-admin-service";

import ExerciseManager from "./exercise-manager";
import { ItemCard, PublishBadge, useLessonSkillsOverview } from "./shared";

const EMPTY = { title: "", content: "", order_index: 1, is_published: false };
const HAS_HTML = /<[a-z][\s\S]*>/i;

/** Grammatik: the lesson's rules (simple HTML: h3, p, ul, table — the
 * server sanitizes it) and below them the auto-graded grammar exercises. */
export default function GrammarManager({ lessonId }: { lessonId: string }) {
  const { data, isLoading, refresh } = useLessonSkillsOverview(lessonId);
  const rules = data?.grammatik ?? [];

  const [editing, setEditing] = useState<AdminGrammar | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [deleting, setDeleting] = useState<AdminGrammar | null>(null);
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
      setError(apiErrorMessage(err, fallback));
      return false;
    } finally {
      setBusy(false);
    }
  }

  function open(item: AdminGrammar | null) {
    setEditing(item);
    setForm(item ? { title: item.title, content: item.content, order_index: item.order_index, is_published: item.is_published }
                 : { ...EMPTY, order_index: rules.length + 1 });
    setError(null);
    setFormOpen(true);
  }

  async function save() {
    const ok = await run(() => saveGrammar(lessonId, { ...form, title: form.title.trim() }, editing?.id), "Speichern fehlgeschlagen.");
    if (ok) setFormOpen(false);
  }

  return (
    <div className="space-y-10">
      <div className="space-y-4" data-testid="admin-grammar">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-[var(--admin-text-secondary)]">
            Regeln: {rules.length} · für Schüler sichtbar: {rules.filter((r) => r.is_published).length}
          </p>
          <AdminButton onClick={() => open(null)} data-testid="grammar-new">
            <Plus size={16} /> Neue Regel
          </AdminButton>
        </div>
        {error && !formOpen && <p className="text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
        {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
        {!isLoading && rules.length === 0 && (
          <p className="rounded-2xl bg-[var(--admin-card)] p-6 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
            Noch keine Grammatikregeln.
          </p>
        )}
        {rules.map((item) => (
          <ItemCard
            key={item.id}
            testId="grammar-item"
            title={`${item.order_index}. ${item.title}`}
            badge={<PublishBadge published={item.is_published} />}
            meta={item.content_id ?? undefined}
            actions={
              <>
                <AdminButton size="sm" variant="ghost" onClick={() => open(item)} aria-label="Bearbeiten">
                  <Pencil size={14} />
                </AdminButton>
                <AdminButton
                  size="sm"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => run(() => saveGrammar(lessonId, { title: item.title, content: item.content, order_index: item.order_index,
                                                                    is_published: !item.is_published }, item.id))}
                  aria-label={item.is_published ? "Verbergen" : "Veröffentlichen"}
                  title={item.is_published ? "Verbergen" : "Veröffentlichen"}
                >
                  {item.is_published ? <EyeOff size={14} /> : <Eye size={14} />}
                </AdminButton>
                <AdminButton size="sm" variant="ghost" onClick={() => setDeleting(item)} aria-label="Löschen">
                  <Trash2 size={14} />
                </AdminButton>
              </>
            }
          >
            {HAS_HTML.test(item.content) ? (
              <div className="prose-editor max-h-64 overflow-auto rounded-lg bg-white/[0.03] p-3 text-sm text-[var(--admin-text-secondary)]"
                   dangerouslySetInnerHTML={{ __html: item.content }} />
            ) : (
              <p className="line-clamp-4 whitespace-pre-line text-sm text-[var(--admin-text-secondary)]">{item.content}</p>
            )}
          </ItemCard>
        ))}
      </div>

      <div>
        <h3 className="mb-3 text-base font-bold text-[var(--admin-text-primary)]">Grammatik-Übungen (automatisch bewertet)</h3>
        <ExerciseManager lessonId={lessonId} skill="GRAMMATIK" label="Grammatik" />
      </div>

      <FormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        title={editing ? "Regel bearbeiten" : "Neue Regel"}
        size="xl"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setFormOpen(false)}>Abbrechen</AdminButton>
            <AdminButton onClick={save} disabled={busy || !form.title.trim() || !form.content.trim()} data-testid="grammar-save">
              {busy ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Titel</label>
            <AdminInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Präsens — Hozirgi zamon" />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
                Inhalt (Text oder einfaches HTML: h3, p, ul/li, strong, table)
              </label>
              <AdminTextarea rows={16} className="resize-y font-mono text-xs" value={form.content}
                             onChange={(e) => setForm({ ...form, content: e.target.value })} spellCheck={false} />
            </div>
            <div>
              <p className="mb-1.5 text-sm font-medium text-[var(--admin-text-primary)]">Vorschau</p>
              {HAS_HTML.test(form.content) ? (
                // preview only — the server sanitizes on save
                <div className="prose-editor max-h-[26rem] overflow-auto rounded-lg bg-white/[0.03] p-3 text-sm text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]"
                     dangerouslySetInnerHTML={{ __html: form.content.replace(/<\s*(script|style|iframe)[\s\S]*?<\/\s*\1\s*>/gi, "") }} />
              ) : (
                <p className="max-h-[26rem] overflow-auto whitespace-pre-line rounded-lg bg-white/[0.03] p-3 text-sm text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]">
                  {form.content || "—"}
                </p>
              )}
            </div>
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

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => !o && setDeleting(null)}
        title="Regel löschen"
        description={`"${deleting?.title}" wird gelöscht.`}
        isPending={busy}
        onConfirm={async () => {
          if (!deleting) return;
          if (await run(() => deleteGrammar(deleting.id), "Löschen fehlgeschlagen.")) setDeleting(null);
        }}
      />
    </div>
  );
}
