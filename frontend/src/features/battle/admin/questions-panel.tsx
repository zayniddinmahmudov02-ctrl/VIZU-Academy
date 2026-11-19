"use client";

import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, FileUp, Plus, Trash2, X } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import {
  createQuestion, deleteQuestion, getQuestions, getQuestionStats, importQuestions, updateQuestion,
  type BattleQuestion, type QuestionImportReport, type QuestionInput, type QuestionLevel, type QuestionStats,
} from "@/features/admin/services/battle-admin-service";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { cn } from "@/lib/utils";

const LEVELS: QuestionLevel[] = ["A1", "A2", "B1", "B2", "C1"];
const STATUS_STYLE: Record<string, string> = {
  published: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/40",
  draft: "bg-amber-500/15 text-amber-300 ring-amber-500/40",
  disabled: "bg-zinc-500/15 text-zinc-300 ring-zinc-500/40",
};
const PROBLEM_DE: Record<string, string> = {
  OPTIONS_NOT_UNIQUE: "Antworten nicht eindeutig (doppelt / richtige Antwort unter den falschen)",
  OPTION_COUNT: "falsche Anzahl Antworten", ANSWER: "richtige Antwort fehlt", WRONG: "falsche Antworten fehlen", PROMPT: "Frage fehlt",
  GAP_MISSING: "Lücke ___ fehlt", ARTICLE_OPTIONS: "nur der / die / das erlaubt", TOPIC: "unbekanntes Thema", TOPIC_KIND: "Thema passt nicht zu Wortschatz/Grammatik",
  CYRILLIC: "kyrillische Buchstaben", UZ_APOSTROPHE: "Apostroph im Usbekischen (o‘ / g‘)", SPACES: "doppelte Leerzeichen", LEVEL: "Level", KIND: "Art", FORMAT: "Format",
};
const problemText = (codes: string[]) => codes.map((c) => PROBLEM_DE[c] ?? c).join(", ");

/** Game Management → Battle → Fragen: the text questions (vocabulary + grammar) per CEFR level. */
export default function QuestionsPanel() {
  const qc = useQueryClient();
  const [filters, setFilters] = useState({ level: "", kind: "", topic: "", status: "", format: "", q: "", problems: false, page: 1 });
  const [editing, setEditing] = useState<BattleQuestion | "new" | null>(null);
  const [showImport, setShowImport] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const stats = useQuery({ queryKey: ["admin-battle-question-stats"], queryFn: getQuestionStats });
  const list = useQuery({ queryKey: ["admin-battle-questions", filters], queryFn: () => getQuestions(filters), placeholderData: keepPreviousData });
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["admin-battle-questions"] });
    qc.invalidateQueries({ queryKey: ["admin-battle-question-stats"] });
    qc.invalidateQueries({ queryKey: ["admin-battle-overview"] });
  };
  const total = list.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / (list.data?.page_size ?? 30)));
  const labels = stats.data?.topic_labels ?? {};
  const formats = stats.data?.format_labels ?? {};

  return (
    <div className="space-y-4" data-testid="admin-battle-questions">
      <StatsCard stats={stats.data} />
      <AdminCard>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <AdminInput placeholder="Suche (Frage / Antwort)" value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value, page: 1 })} data-testid="bq-search" />
          <AdminSelect value={filters.level} onChange={(e) => setFilters({ ...filters, level: e.target.value, page: 1 })} aria-label="Level" data-testid="bq-filter-level">
            <option value="">Alle Level</option>{LEVELS.map((l) => <option key={l}>{l}</option>)}
          </AdminSelect>
          <AdminSelect value={filters.kind} onChange={(e) => setFilters({ ...filters, kind: e.target.value, page: 1 })} aria-label="Art" data-testid="bq-filter-kind">
            <option value="">Wortschatz + Grammatik</option><option value="vocab">Wortschatz</option><option value="grammar">Grammatik</option>
          </AdminSelect>
          <AdminSelect value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })} aria-label="Status" data-testid="bq-filter-status">
            <option value="">Alle Status</option><option value="published">aktiv (published)</option><option value="draft">Entwurf</option><option value="disabled">deaktiviert</option>
          </AdminSelect>
          <AdminSelect value={filters.topic} onChange={(e) => setFilters({ ...filters, topic: e.target.value, page: 1 })} aria-label="Thema">
            <option value="">Alle Themen</option>{Object.entries(labels).sort((a, b) => a[1].de.localeCompare(b[1].de)).map(([k, l]) => <option key={k} value={k}>{l.de}</option>)}
          </AdminSelect>
          <AdminSelect value={filters.format} onChange={(e) => setFilters({ ...filters, format: e.target.value, page: 1 })} aria-label="Format">
            <option value="">Alle Formate</option>{Object.entries(formats).map(([k, f]) => <option key={k} value={k}>{k} — {f.de}</option>)}
          </AdminSelect>
          <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
            <input type="checkbox" checked={filters.problems} onChange={(e) => setFilters({ ...filters, problems: e.target.checked, page: 1 })} data-testid="bq-filter-problems" />
            nur fehlerhafte Fragen
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <AdminButton size="sm" onClick={() => setEditing("new")} data-testid="bq-new"><Plus size={14} /> Neue Frage</AdminButton>
            <AdminButton size="sm" variant="secondary" onClick={() => setShowImport(true)} data-testid="bq-import-open"><FileUp size={14} /> Import</AdminButton>
          </div>
        </div>
        <p className="mt-2 text-sm text-[var(--admin-text-secondary)]" data-testid="bq-total">{total} Fragen</p>
        {msg && <p role="status" className="mt-2 text-sm text-amber-300">{msg}</p>}
      </AdminCard>

      <AdminCard className="overflow-x-auto p-0">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="text-xs text-[var(--admin-text-muted)]">
            <tr><th className="p-3">Level</th><th>Thema</th><th>Format</th><th>Frage</th><th>Richtige Antwort</th><th>Status</th><th /></tr>
          </thead>
          <tbody className="text-[var(--admin-text-primary)]">
            {list.data?.items.map((q) => (
              <tr key={q.id} className="cursor-pointer border-t border-[var(--admin-border)] hover:bg-[var(--admin-hover)]" onClick={() => setEditing(q)} data-testid="bq-row">
                <td className="p-3 font-semibold">{q.level}</td>
                <td className="text-xs">{labels[q.topic]?.de ?? q.topic}<span className="block text-[var(--admin-text-muted)]">{q.kind === "grammar" ? "Grammatik" : "Wortschatz"}</span></td>
                <td className="text-xs">{q.format}</td>
                <td className="max-w-[340px] truncate pr-2" title={q.prompt}>{q.prompt}</td>
                <td className="max-w-[200px] truncate pr-2 font-semibold" title={q.answer}>{q.answer}</td>
                <td><span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1", STATUS_STYLE[q.status])}>{q.status}</span></td>
                <td className="pr-3">{q.problems.length > 0 && <span title={problemText(q.problems)}><AlertTriangle size={15} className="text-amber-400" /></span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.data && list.data.items.length === 0 && <p className="p-4 text-sm text-[var(--admin-text-secondary)]">Keine Fragen gefunden.</p>}
      </AdminCard>
      <div className="flex items-center justify-center gap-3 text-sm text-[var(--admin-text-secondary)]">
        <AdminButton size="sm" variant="ghost" disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>Zurück</AdminButton>
        {filters.page}/{pages}
        <AdminButton size="sm" variant="ghost" disabled={filters.page >= pages} onClick={() => setFilters({ ...filters, page: filters.page + 1 })}>Weiter</AdminButton>
      </div>

      {editing && (
        <QuestionEditor question={editing === "new" ? null : editing} stats={stats.data} onClose={() => setEditing(null)}
                        onSaved={(text) => { setMsg(text); setEditing(null); refresh(); }} />
      )}
      {showImport && <ImportDialog onClose={() => setShowImport(false)} onDone={(text) => { setMsg(text); refresh(); }} />}
    </div>
  );
}

function StatsCard({ stats }: { stats?: QuestionStats }) {
  if (!stats) return <AdminCard><p className="text-sm text-[var(--admin-text-secondary)]">Lädt…</p></AdminCard>;
  return (
    <AdminCard>
      <h2 className="mb-3 text-sm font-bold text-[var(--admin-text-primary)]">Fragen je Level (Ziel: mindestens {stats.min_per_level} aktive Fragen je Level, Bildwörter separat)</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm" data-testid="bq-stats">
          <thead className="text-xs text-[var(--admin-text-muted)]">
            <tr><th className="py-1">Level</th><th>Gesamt</th><th>Wortschatz</th><th>Grammatik</th><th>Aktiv</th><th>Entwurf</th><th>Deaktiviert</th><th>Doppelt</th><th>Fehlerhaft</th></tr>
          </thead>
          <tbody className="text-[var(--admin-text-primary)]">
            {LEVELS.map((lv) => {
              const r = stats.levels[lv];
              const ok = r && r.published >= stats.min_per_level;
              return (
                <tr key={lv} className="border-t border-[var(--admin-border)]" data-testid={`bq-stats-${lv}`}>
                  <td className="py-1.5 font-semibold">{lv}</td><td>{r?.total ?? 0}</td><td>{r?.vocab ?? 0}</td><td>{r?.grammar ?? 0}</td>
                  <td className={ok ? "font-semibold text-emerald-400" : "font-semibold text-amber-400"} data-testid={`bq-active-${lv}`}>{r?.published ?? 0}</td>
                  <td>{r?.draft ?? 0}</td><td>{r?.disabled ?? 0}</td>
                  <td className={r?.duplicates ? "text-amber-400" : ""}>{r?.duplicates ?? 0}</td>
                  <td className={r?.problems ? "text-red-400" : ""}>{r?.problems ?? 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-[var(--admin-text-muted)]">Doppelt = gleiche Frage mit gleicher Antwort in einem anderen Format. Dieselbe Frage zweimal im selben Format verhindert die Datenbank.</p>
    </AdminCard>
  );
}

function QuestionEditor({ question, stats, onClose, onSaved }: { question: BattleQuestion | null; stats?: QuestionStats; onClose: () => void; onSaved: (msg: string) => void }) {
  const [form, setForm] = useState<QuestionInput>(question ? {
    level: question.level, format: question.format, topic: question.topic, prompt: question.prompt, answer: question.answer, wrong: [...question.wrong],
    status: question.status, hint: question.hint, explanation: question.explanation,
  } : { level: "A2", format: "grammar", topic: "akk_dat", prompt: "", answer: "", wrong: ["", "", ""], status: "draft", hint: null, explanation: null });
  const [error, setError] = useState<string | null>(null);
  const options = stats?.format_labels[form.format]?.options ?? 4;
  const wrong = Array.from({ length: options - 1 }, (_, i) => form.wrong[i] ?? "");
  const payload = { ...form, wrong, hint: form.hint || null, explanation: form.explanation || null };
  const save = useMutation({
    mutationFn: () => (question ? updateQuestion(question.id, payload) : createQuestion(payload)),
    onSuccess: () => onSaved(question ? "Frage gespeichert." : "Frage angelegt."),
    onError: (e) => setError(apiErrorMessage(e, "Speichern fehlgeschlagen.")),
  });
  const remove = useMutation({
    mutationFn: () => deleteQuestion(question!.id),
    onSuccess: () => onSaved("Frage gelöscht."),
    onError: (e) => setError(apiErrorMessage(e, "Löschen fehlgeschlagen.")),
  });
  const set = (patch: Partial<QuestionInput>) => setForm({ ...form, ...patch });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <aside className="h-full w-full max-w-xl overflow-y-auto bg-[var(--admin-bg)] p-5 shadow-2xl ring-1 ring-[var(--admin-border)]" onClick={(e) => e.stopPropagation()} data-testid="bq-editor">
        <div className="mb-4 flex items-start justify-between gap-3">
          <h2 className="text-xl font-bold text-[var(--admin-text-primary)]">{question ? "Frage bearbeiten" : "Neue Frage"}</h2>
          <AdminButton size="sm" variant="ghost" onClick={onClose} aria-label="Schließen"><X size={16} /></AdminButton>
        </div>
        {question && question.problems.length > 0 && <p className="mb-3 rounded-lg bg-amber-500/10 p-2 text-sm text-amber-300">Probleme: {problemText(question.problems)}</p>}
        <div className="grid grid-cols-2 gap-2">
          <AdminSelect value={form.level} onChange={(e) => set({ level: e.target.value as QuestionLevel })} aria-label="Level" data-testid="bq-edit-level">
            {LEVELS.map((l) => <option key={l}>{l}</option>)}
          </AdminSelect>
          <AdminSelect value={form.status} onChange={(e) => set({ status: e.target.value as QuestionInput["status"] })} aria-label="Status" data-testid="bq-edit-status">
            <option value="draft">Entwurf</option><option value="published">aktiv (published)</option><option value="disabled">deaktiviert</option>
          </AdminSelect>
          <AdminSelect value={form.format} onChange={(e) => set({ format: e.target.value })} aria-label="Format" data-testid="bq-edit-format">
            {Object.entries(stats?.format_labels ?? {}).map(([k, f]) => <option key={k} value={k}>{k} — {f.de}</option>)}
          </AdminSelect>
          <AdminSelect value={form.topic} onChange={(e) => set({ topic: e.target.value })} aria-label="Thema" data-testid="bq-edit-topic">
            {Object.entries(stats?.topic_labels ?? {}).sort((a, b) => a[1].de.localeCompare(b[1].de)).map(([k, l]) => (
              <option key={k} value={k}>{l.de} ({l.kind === "grammar" ? "Grammatik" : "Wortschatz"})</option>
            ))}
          </AdminSelect>
        </div>
        <label className="mt-3 block text-xs font-semibold text-[var(--admin-text-secondary)]">Frage (Lücke als ___)
          <AdminInput value={form.prompt} onChange={(e) => set({ prompt: e.target.value })} data-testid="bq-edit-prompt" />
        </label>
        <label className="mt-2 block text-xs font-semibold text-[var(--admin-text-secondary)]">Hinweis (optional, z. B. usbekischer Satz)
          <AdminInput value={form.hint ?? ""} onChange={(e) => set({ hint: e.target.value })} />
        </label>
        <label className="mt-2 block text-xs font-semibold text-emerald-300">Richtige Antwort
          <AdminInput value={form.answer} onChange={(e) => set({ answer: e.target.value })} data-testid="bq-edit-answer" />
        </label>
        {wrong.map((w, i) => (
          <label key={i} className="mt-2 block text-xs font-semibold text-red-300">Falsche Antwort {i + 1}
            <AdminInput value={w} onChange={(e) => { const next = [...wrong]; next[i] = e.target.value; set({ wrong: next }); }} data-testid={`bq-edit-wrong-${i}`} />
          </label>
        ))}
        <label className="mt-2 block text-xs font-semibold text-[var(--admin-text-secondary)]">Erklärung nach der Runde (optional)
          <AdminInput value={form.explanation ?? ""} onChange={(e) => set({ explanation: e.target.value })} />
        </label>
        {error && <p role="alert" className="mt-3 text-sm text-red-400" data-testid="bq-edit-error">{error}</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          <AdminButton onClick={() => { setError(null); save.mutate(); }} disabled={save.isPending} data-testid="bq-edit-save">Speichern</AdminButton>
          {question && (
            <AdminButton variant="ghost" onClick={() => { if (window.confirm("Diese Frage endgültig löschen? (Laufende Kämpfe behalten ihre Kopie.)")) remove.mutate(); }}
                         disabled={remove.isPending} data-testid="bq-edit-delete"><Trash2 size={14} /> Löschen</AdminButton>
          )}
        </div>
        <p className="mt-3 text-xs text-[var(--admin-text-muted)]">Genau eine richtige Antwort; die falschen müssen wirklich falsch sein. Dieselbe Frage darf es je Level nur einmal geben.</p>
      </aside>
    </div>
  );
}

function ImportDialog({ onClose, onDone }: { onClose: () => void; onDone: (msg: string) => void }) {
  const [text, setText] = useState("");
  const [publish, setPublish] = useState(false);
  const [report, setReport] = useState<QuestionImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const parse = (): unknown[] | null => {
    try {
      const data = JSON.parse(text);
      return Array.isArray(data) ? data : Array.isArray(data?.questions) ? data.questions : null;
    } catch {
      return null;
    }
  };
  const run = useMutation({
    mutationFn: (apply: boolean) => {
      const items = parse();
      if (!items) throw new Error("JSON: eine Liste von Fragen oder {\"questions\": [...]} erwartet.");
      return importQuestions(items, apply, publish);
    },
    onSuccess: (r, apply) => { setReport(r); setError(null); if (apply) onDone(`${r.added} Fragen importiert (${r.duplicates} doppelt, ${r.invalid} fehlerhaft übersprungen).`); },
    onError: (e) => setError(e instanceof Error && !("response" in e) ? e.message : apiErrorMessage(e, "Import fehlgeschlagen.")),
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <aside className="h-full w-full max-w-xl overflow-y-auto bg-[var(--admin-bg)] p-5 shadow-2xl ring-1 ring-[var(--admin-border)]" onClick={(e) => e.stopPropagation()} data-testid="bq-import">
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="text-xl font-bold text-[var(--admin-text-primary)]">Fragen importieren (JSON)</h2>
          <AdminButton size="sm" variant="ghost" onClick={onClose} aria-label="Schließen"><X size={16} /></AdminButton>
        </div>
        <p className="mb-2 text-xs text-[var(--admin-text-secondary)]">
          Liste von Objekten mit level, format, topic, prompt, answer, wrong (2–3), optional hint, explanation. Zuerst prüfen, dann importieren —
          doppelte und fehlerhafte Fragen werden übersprungen, vorhandene Fragen nie geändert.
        </p>
        <textarea value={text} onChange={(e) => { setText(e.target.value); setReport(null); }} rows={12} data-testid="bq-import-text"
                  className="w-full rounded-xl bg-[var(--admin-card)] p-3 font-mono text-xs text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border)]"
                  placeholder='[{"level": "A2", "format": "grammar", "topic": "akk_dat", "prompt": "Ich helfe ___ Mann.", "answer": "dem", "wrong": ["den", "der", "des"]}]' />
        <label className="mt-2 flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
          <input type="checkbox" checked={publish} onChange={(e) => setPublish(e.target.checked)} data-testid="bq-import-publish" /> sofort aktiv (sonst als Entwurf)
        </label>
        <div className="mt-3 flex gap-2">
          <AdminButton variant="secondary" onClick={() => run.mutate(false)} disabled={!text || run.isPending} data-testid="bq-import-check">Prüfen</AdminButton>
          <AdminButton onClick={() => run.mutate(true)} disabled={!report || report.valid === 0 || run.isPending} data-testid="bq-import-apply">Importieren</AdminButton>
        </div>
        {error && <p role="alert" className="mt-3 text-sm text-red-400">{error}</p>}
        {report && (
          <div className="mt-3 space-y-1 text-sm text-[var(--admin-text-primary)]" data-testid="bq-import-report">
            <p>{report.total} gelesen · <b className="text-emerald-400">{report.valid} gültig</b> · {report.duplicates} doppelt · <span className="text-red-400">{report.invalid} fehlerhaft</span>{report.added ? ` · ${report.added} importiert` : ""}</p>
            {report.errors.slice(0, 20).map((e) => <p key={e.row} className="text-xs text-red-300">Zeile {e.row}: {problemText(e.problems)}{e.prompt ? ` — ${e.prompt}` : ""}</p>)}
          </div>
        )}
      </aside>
    </div>
  );
}
