"use client";

import { useMemo, useRef, useState } from "react";
import { Download, Pencil, Plus, Search, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  apiErrorMessage,
  deleteWord,
  downloadWordsCsv,
  importWordsCsv,
  saveWord,
  type AdminWord,
  type WordImportReport,
  type WordInput,
} from "@/features/admin/services/lesson-skills-admin-service";

import ExerciseManager from "./exercise-manager";
import { useLessonSkillsOverview } from "./shared";

const EMPTY: WordInput = { german_word: "", translation: "", article: null, plural: null, example_sentence: null, example_translation: null,
                           word_type: null, verb_praeteritum: null, verb_partizip_ii: null, verb_auxiliary: null, audio_url: null,
                           order_index: null, is_published: true };
const WORD_TYPES = ["Nomen", "Verb", "Adjektiv", "Adverb", "Präposition", "Konjunktion", "Pronomen", "Wendung", "Numerale", "Partikel"];
const FIELD_LABEL: Record<string, string> = {
  word_type: "Wortart", plural: "Plural", verb_praeteritum: "Präteritum", verb_partizip_ii: "Partizip II", verb_auxiliary: "Hilfsverb",
  example_sentence: "Beispiel", example_translation: "Übersetzung des Beispiels",
};

/** Wortschatz: the lesson's words (book + verified Wörterbuch data, missing
 * fields marked), CSV export / import (preview first) and the auto-graded
 * Wortschatz tests (exercise sets). */
export default function WordManager({ lessonId }: { lessonId: string }) {
  const { data, isLoading, refresh } = useLessonSkillsOverview(lessonId);
  const words = useMemo(() => [...(data?.wortschatz ?? [])].sort((a, b) => a.order_index - b.order_index), [data]);
  const fileRef = useRef<HTMLInputElement>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [report, setReport] = useState<WordImportReport | null>(null);
  const [onlyMissing, setOnlyMissing] = useState(false);

  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<AdminWord | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<WordInput>(EMPTY);
  const [deleting, setDeleting] = useState<AdminWord | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = onlyMissing ? words.filter((w) => w.missing?.length) : words;
    return q ? list.filter((w) => `${w.article ?? ""} ${w.german_word} ${w.translation}`.toLowerCase().includes(q)) : list;
  }, [words, query, onlyMissing]);

  async function exportCsv() {
    await run(async () => {
      const blob = await downloadWordsCsv(lessonId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `wortschatz-${lessonId}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }, "Export fehlgeschlagen.");
  }

  async function previewImport(file: File) {
    setImportFile(file);
    setReport(null);
    await run(async () => setReport(await importWordsCsv(lessonId, file, false)), "CSV konnte nicht gelesen werden.");
  }

  async function applyImport() {
    if (!importFile) return;
    const ok = await run(async () => setReport(await importWordsCsv(lessonId, importFile, true)), "Import fehlgeschlagen.");
    if (ok) setImportFile(null);
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

  function open(item: AdminWord | null) {
    setEditing(item);
    setForm(item ? { german_word: item.german_word, translation: item.translation, article: item.article, plural: item.plural,
                     example_sentence: item.example_sentence, example_translation: item.example_translation, word_type: item.word_type,
                     verb_praeteritum: item.verb_praeteritum, verb_partizip_ii: item.verb_partizip_ii, verb_auxiliary: item.verb_auxiliary,
                     audio_url: item.audio_url, order_index: item.order_index, is_published: item.is_published } : EMPTY);
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
            {words.length} Wörter · sichtbar: {words.filter((w) => w.is_published).length} · unvollständig:{" "}
            {words.filter((w) => w.missing?.length).length}
          </p>
          <div className="flex flex-wrap gap-2">
            <div className="relative w-56">
              <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
              <AdminInput className="pl-8" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Suchen…" aria-label="Wort suchen" />
            </div>
            <label className="flex cursor-pointer items-center gap-2 text-xs text-[var(--admin-text-secondary)]">
              <AdminCheckbox checked={onlyMissing} onCheckedChange={setOnlyMissing} /> nur unvollständige
            </label>
            <AdminButton variant="ghost" onClick={exportCsv} disabled={busy} data-testid="words-export">
              <Download size={15} /> CSV
            </AdminButton>
            <AdminButton variant="ghost" onClick={() => fileRef.current?.click()} disabled={busy} data-testid="words-import">
              <Upload size={15} /> CSV-Import
            </AdminButton>
            <input ref={fileRef} type="file" accept=".csv,text/csv" className="hidden" data-testid="words-import-file"
                   onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) void previewImport(f); }} />
            <AdminButton onClick={() => open(null)} data-testid="word-new">
              <Plus size={16} /> Neues Wort
            </AdminButton>
          </div>
        </div>
        {report && (
          <div className="space-y-2 rounded-2xl bg-[var(--admin-card)] p-4 text-sm ring-1 ring-[var(--admin-border)]" data-testid="words-import-report">
            <p className="font-semibold text-[var(--admin-text-primary)]">
              {report.applied ? "Import ausgeführt" : "Vorschau (noch nichts gespeichert)"}: {report.rows} Zeilen · neu {report.created} · geändert{" "}
              {report.updated} · unverändert {report.unchanged}
            </p>
            {report.errors.length > 0 && (
              <ul className="list-disc space-y-0.5 pl-5 text-[var(--admin-danger)]">
                {report.errors.slice(0, 20).map((e) => <li key={e}>{e}</li>)}
              </ul>
            )}
            {!report.applied && report.errors.length === 0 && (report.created > 0 || report.updated > 0) && (
              <AdminButton size="sm" onClick={applyImport} disabled={busy} data-testid="words-import-apply">Import ausführen</AdminButton>
            )}
          </div>
        )}
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
                  <th className="px-3 py-2.5">Wortart</th>
                  <th className="px-3 py-2.5">Plural</th>
                  <th className="px-3 py-2.5">{"O'zbekcha"}</th>
                  <th className="px-3 py-2.5">Fehlt</th>
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
                    <td className="px-3 py-2 text-xs text-[var(--admin-text-secondary)]">{w.word_type ?? "—"}</td>
                    <td className="px-3 py-2 text-[var(--admin-text-secondary)]">{w.plural ?? "—"}</td>
                    <td className="px-3 py-2 text-[var(--admin-text-secondary)]">{w.translation}</td>
                    <td className="px-3 py-2 text-xs text-amber-600" data-testid="word-missing">
                      {w.missing?.length ? w.missing.map((m) => FIELD_LABEL[m] ?? m).join(", ") : "—"}
                    </td>
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
        <h3 className="mb-3 text-base font-bold text-[var(--admin-text-primary)]">Wortschatz-Übungen und -Tests (automatisch bewertet)</h3>
        <p className="mb-3 text-xs text-[var(--admin-text-muted)]">
          Quelle „VIZU“ = Tests aus den Wörtern dieser Lektion (Schüler: Wortschatz → Tests), „Buch“ = Übungen aus dem Buch (Wortschatz → Übungen).
        </p>
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
            {field("plural", "Plural (nur belegte Form)")}
            {field("translation", "O'zbekcha", "oila")}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Wortart</label>
              <AdminSelect value={form.word_type ?? ""} onChange={(e) => setForm({ ...form, word_type: e.target.value || null })} aria-label="Wortart">
                <option value="">—</option>
                {WORD_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </AdminSelect>
            </div>
            {form.word_type === "Verb" && (
              <div>
                <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">Hilfsverb</label>
                <AdminSelect value={form.verb_auxiliary ?? ""} onChange={(e) => setForm({ ...form, verb_auxiliary: e.target.value || null })} aria-label="Hilfsverb">
                  <option value="">—</option>
                  <option value="haben">haben</option>
                  <option value="sein">sein</option>
                </AdminSelect>
              </div>
            )}
          </div>
          {form.word_type === "Verb" && (
            <div className="grid gap-3 sm:grid-cols-2">
              {field("verb_praeteritum", "Präteritum (er/sie/es)", "arbeitete")}
              {field("verb_partizip_ii", "Partizip II", "gearbeitet")}
            </div>
          )}
          {field("example_sentence", "Beispielsatz (optional)")}
          {field("example_translation", "Übersetzung des Beispiels (optional)")}
          {field("audio_url", "Audio-URL (optional; sonst Browser-Aussprache)")}
          {editing && Object.keys(editing.sources ?? {}).length > 0 && (
            <p className="text-xs text-[var(--admin-text-muted)]">
              Herkunft: {Object.entries(editing.sources).map(([k, v]) => `${FIELD_LABEL[k] ?? k} ← ${v}`).join(" · ")}
            </p>
          )}
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
