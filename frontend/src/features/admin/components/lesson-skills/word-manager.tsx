"use client";

import { useMemo, useState } from "react";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import { apiErrorMessage, deleteWord, saveWord, type AdminWord, type WordInput } from "@/features/admin/services/lesson-skills-admin-service";

import ExerciseManager from "./exercise-manager";
import { useLessonSkillsOverview } from "./shared";

const EMPTY: WordInput = { german_word: "", translation: "", article: null, plural: null, example_sentence: null, example_translation: null,
                           order_index: null, is_published: true };

/** Wortschatz: the lesson's words (from the book) and the practice sets. */
export default function WordManager({ lessonId }: { lessonId: string }) {
  const { data, isLoading, refresh } = useLessonSkillsOverview(lessonId);
  const words = useMemo(() => [...(data?.wortschatz ?? [])].sort((a, b) => a.order_index - b.order_index), [data]);

  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<AdminWord | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<WordInput>(EMPTY);
  const [deleting, setDeleting] = useState<AdminWord | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? words.filter((w) => `${w.article ?? ""} ${w.german_word} ${w.translation}`.toLowerCase().includes(q)) : words;
  }, [words, query]);

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

  function open(item: AdminWord | null) {
    setEditing(item);
    setForm(item ? { german_word: item.german_word, translation: item.translation, article: item.article, plural: item.plural,
                     example_sentence: item.example_sentence, example_translation: item.example_translation, order_index: item.order_index,
                     is_published: item.is_published } : EMPTY);
    setError(null);
    setFormOpen(true);
  }

  async function save() {
    const ok = await run(() => saveWord(lessonId, form, editing?.id), "Speichern fehlgeschlagen.");
    if (ok) setFormOpen(false);
  }

  const field = (key: keyof WordInput, label: string, placeholder = "") => (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">{label}</label>
      <AdminInput value={(form[key] as string | null) ?? ""} placeholder={placeholder}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value || null })} />
    </div>
  );

  return (
    <div className="space-y-10">
      <div className="space-y-4" data-testid="admin-words">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-[var(--admin-text-secondary)]">
            {words.length} Wörter · sichtbar: {words.filter((w) => w.is_published).length}
          </p>
          <div className="flex flex-wrap gap-2">
            <div className="relative w-56">
              <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
              <AdminInput className="pl-8" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Suchen…" aria-label="Wort suchen" />
            </div>
            <AdminButton onClick={() => open(null)} data-testid="word-new">
              <Plus size={16} /> Neues Wort
            </AdminButton>
          </div>
        </div>
        {error && !formOpen && <p className="text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
        {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
        {!isLoading && words.length === 0 && (
          <p className="rounded-2xl bg-[var(--admin-card)] p-6 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
            Noch keine Wörter.
          </p>
        )}
        {shown.length > 0 && (
          <div className="overflow-x-auto rounded-2xl bg-[var(--admin-card)] ring-1 ring-[var(--admin-border)]">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--admin-border)] text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
                  <th className="px-4 py-2.5">#</th>
                  <th className="px-3 py-2.5">Deutsch</th>
                  <th className="px-3 py-2.5">Plural</th>
                  <th className="px-3 py-2.5">{"O'zbekcha"}</th>
                  <th className="px-3 py-2.5">Status</th>
                  <th className="w-20" />
                </tr>
              </thead>
              <tbody>
                {shown.map((w) => (
                  <tr key={w.id} className="border-b border-[var(--admin-border)] last:border-0" data-testid="word-row">
                    <td className="px-4 py-2 text-[var(--admin-text-muted)]">{w.order_index}</td>
                    <td className="px-3 py-2 text-[var(--admin-text-primary)]">
                      {w.article && <span className="mr-1 text-[var(--admin-text-muted)]">{w.article}</span>}
                      <span className="font-semibold">{w.german_word}</span>
                    </td>
                    <td className="px-3 py-2 text-[var(--admin-text-secondary)]">{w.plural ?? "—"}</td>
                    <td className="px-3 py-2 text-[var(--admin-text-secondary)]">{w.translation}</td>
                    <td className="px-3 py-2 text-xs">{w.is_published ? "sichtbar" : <span className="text-[var(--admin-text-muted)]">verborgen</span>}</td>
                    <td className="px-2 py-2 text-right">
                      <AdminButton size="sm" variant="ghost" onClick={() => open(w)} aria-label="Bearbeiten"><Pencil size={13} /></AdminButton>
                      <AdminButton size="sm" variant="ghost" onClick={() => setDeleting(w)} aria-label="Löschen"><Trash2 size={13} /></AdminButton>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div>
        <h3 className="mb-3 text-base font-bold text-[var(--admin-text-primary)]">Wortschatz-Übungen (automatisch bewertet)</h3>
        <ExerciseManager lessonId={lessonId} skill="WORTSCHATZ" label="Wortschatz" />
      </div>

      <FormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        title={editing ? "Wort bearbeiten" : "Neues Wort"}
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setFormOpen(false)}>Abbrechen</AdminButton>
            <AdminButton onClick={save} disabled={busy || !form.german_word.trim() || !form.translation.trim()} data-testid="word-save">
              {busy ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
          <div className="grid gap-3 sm:grid-cols-[8rem_1fr]">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Artikel</label>
              <AdminSelect value={form.article ?? ""} onChange={(e) => setForm({ ...form, article: e.target.value || null })} aria-label="Artikel">
                <option value="">—</option>
                <option value="der">der</option>
                <option value="die">die</option>
                <option value="das">das</option>
              </AdminSelect>
            </div>
            {field("german_word", "Wort (ohne Artikel)", "Familie")}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {field("plural", "Plural (optional, nur wenn im Buch)")}
            {field("translation", "O'zbekcha", "oila")}
          </div>
          {field("example_sentence", "Beispielsatz (optional)")}
          {field("example_translation", "Übersetzung des Beispiels (optional)")}
          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox checked={form.is_published} onCheckedChange={(checked) => setForm({ ...form, is_published: checked })} />
            <span className="text-sm text-[var(--admin-text-secondary)]">Für Schüler sichtbar</span>
          </label>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => !o && setDeleting(null)}
        title="Wort löschen"
        description={`"${deleting?.german_word}" wird gelöscht.`}
        isPending={busy}
        onConfirm={async () => {
          if (!deleting) return;
          if (await run(() => deleteWord(deleting.id), "Löschen fehlgeschlagen.")) setDeleting(null);
        }}
      />
    </div>
  );
}
