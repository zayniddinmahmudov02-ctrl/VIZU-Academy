"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileInput, Save, TriangleAlert } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { getAnswerKeys, importAnswerKeys, putAnswerKeys } from "@/features/vorbereitung/services/multilevel-exam-service";
import type { AnswerKeyItem, AnswerKeyTable, KeyImportResult, KeySection } from "@/features/vorbereitung/types/multilevel-exam.types";

interface TestOption { id: string; title: string; status: string }

const SECTION_DE: Record<KeySection, string> = { HOEREN: "Hören", LESEN: "Lesen" };
const TYPE_DE: Record<string, string> = { SINGLE_CHOICE: "a/b/c", TRUE_FALSE: "Richtig / Falsch", MATCHING: "Zuordnung", DROPDOWN: "Auswahl" };
const SOURCE_DE: Record<string, string> = { entered: "gespeichert", derived: "aus Markierung" };

/** letters a question accepts: r / f / a / b for true-false, a … (a + options − 1) otherwise (the server checks the same rules) */
const allowed = (item: AnswerKeyItem): string[] => (item.type === "TRUE_FALSE" ? ["r", "f", "a", "b"] : Array.from({ length: item.option_count }, (_, i) => String.fromCharCode(97 + i)));
const isValid = (item: AnswerKeyItem, value: string) => value === "" || allowed(item).includes(value.toLowerCase());

/** Admin → Multilevel → Answer Key: one numbered table per Modelltest and section (Hören first; Lesen uses the same tool). The letters are saved exactly as typed
 * (R stays R, b stays b), compared without regard to case; the count of questions and answers is checked before anything is saved. */
export default function MultilevelAnswerKeys({ tests }: { tests: TestOption[] }) {
  const [testId, setTestId] = useState<string>(tests[0]?.id ?? "");
  const [section, setSection] = useState<KeySection>("HOEREN");
  const current = tests.find((t) => t.id === testId) ?? tests[0];
  if (!current) return null;
  return (
    <AdminCard>
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-[var(--admin-text-primary)]">Answer Key (Lösungsschlüssel)</h2>
          <p className="text-xs text-[var(--admin-text-muted)]">Pro Modelltest eine nummerierte Tabelle. Antworten werden so gespeichert, wie sie eingegeben sind; Groß- und Kleinschreibung zählt beim Prüfen nicht.</p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <div className="w-56">
            <AdminLabel htmlFor="keys-test">Modelltest</AdminLabel>
            <AdminSelect id="keys-test" value={current.id} onChange={(e) => setTestId(e.target.value)} data-testid="keys-test">
              {tests.map((t) => <option key={t.id} value={t.id}>{t.title} · {t.status === "PUBLISHED" ? "veröffentlicht" : "Entwurf"}</option>)}
            </AdminSelect>
          </div>
          <div className="flex gap-1" role="tablist" aria-label="Teil">
            {(Object.keys(SECTION_DE) as KeySection[]).map((s) => (
              <AdminButton key={s} size="sm" variant={section === s ? "primary" : "secondary"} onClick={() => setSection(s)} role="tab" aria-selected={section === s} data-testid={`keys-section-${s}`}>{SECTION_DE[s]}</AdminButton>
            ))}
          </div>
        </div>
      </div>
      <KeyEditor key={`${current.id}-${section}`} testId={current.id} section={section} />
    </AdminCard>
  );
}

function KeyEditor({ testId, section }: { testId: string; section: KeySection }) {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["multilevel-answer-keys", testId, section], queryFn: () => getAnswerKeys(testId, section), retry: false });
  const [draft, setDraft] = useState<Record<number, string>>({});
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [importText, setImportText] = useState("");
  const [checked, setChecked] = useState<KeyImportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const table = query.data;

  const store = (next: AnswerKeyTable) => {
    queryClient.setQueryData(["multilevel-answer-keys", testId, section], next);
    void queryClient.invalidateQueries({ queryKey: ["mock-exam-model-tests"] });
  };

  if (query.isLoading) return <p className="text-sm text-[var(--admin-text-muted)]">Laden …</p>;
  if (query.isError || !table) return <p role="alert" className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(query.error, "Der Answer Key konnte nicht geladen werden.")}</p>;

  const changed = table.items.filter((i) => draft[i.number] !== undefined && draft[i.number] !== "" && draft[i.number] !== (i.answer ?? ""));
  const invalid = table.items.filter((i) => draft[i.number] !== undefined && !isValid(i, draft[i.number]));

  async function save() {
    setMessage(null);
    if (invalid.length) {
      setMessage({ ok: false, text: `Ungültige Antwort bei Nr. ${invalid.map((i) => i.number).join(", ")}.` });
      return;
    }
    setBusy(true);
    try {
      store(await putAnswerKeys(testId, section, Object.fromEntries(changed.map((i) => [String(i.number), draft[i.number]]))));
      setDraft({});
      setMessage({ ok: true, text: `${changed.length} Antwort(en) gespeichert.` });
    } catch (err) {
      setMessage({ ok: false, text: apiErrorMessage(err, "Speichern fehlgeschlagen.") });
    } finally {
      setBusy(false);
    }
  }

  async function check() {
    setMessage(null);
    setBusy(true);
    try {
      setChecked(await importAnswerKeys(testId, section, importText, true));
    } catch (err) {
      setChecked(null);
      setMessage({ ok: false, text: apiErrorMessage(err, "Prüfen fehlgeschlagen.") });
    } finally {
      setBusy(false);
    }
  }

  async function apply() {
    setBusy(true);
    try {
      const result = await importAnswerKeys(testId, section, importText, false);
      setChecked(result);
      if (result.applied && result.table) {
        store(result.table);
        setDraft({});
        setMessage({ ok: true, text: `${result.given} Antworten übernommen.` });
      }
    } catch (err) {
      setMessage({ ok: false, text: apiErrorMessage(err, "Übernehmen fehlgeschlagen.") });
    } finally {
      setBusy(false);
    }
  }

  const r = table.readiness;
  return (
    <div className="space-y-4" data-testid="keys-card">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-[var(--admin-text-primary)]" data-testid="keys-summary" data-complete={table.complete ? "1" : "0"}>
        <span className="font-semibold">{table.title} · {SECTION_DE[section]}</span>
        <span>{table.question_count} Fragen</span>
        <span>{table.keys_set} Antworten</span>
        {table.complete
          ? <span className="inline-flex items-center gap-1 text-[var(--admin-success)]"><CheckCircle2 size={14} /> vollständig</span>
          : <span className="inline-flex items-center gap-1 text-[var(--admin-warning)]"><TriangleAlert size={14} /> {table.question_count - table.keys_set} fehlen</span>}
        {table.attempts > 0 && <span className="text-xs text-[var(--admin-text-muted)]">{table.attempts} Versuche: bereits gespeicherte Ergebnisse ändern sich nicht.</span>}
      </div>

      <div className="max-h-[28rem] overflow-auto rounded-lg ring-1 ring-[var(--admin-border)]">
        <table className="w-full min-w-[560px] text-left text-sm text-[var(--admin-text-primary)]" data-testid="keys-table">
          <thead className="sticky top-0 bg-[var(--admin-card)] text-xs text-[var(--admin-text-muted)]">
            <tr><th className="px-3 py-2">№</th><th>Teil</th><th>Frage</th><th>Typ</th><th className="w-24">Correct Answer</th><th>Gewählte Option</th><th>Quelle</th></tr>
          </thead>
          <tbody>
            {table.items.map((item) => {
              const value = draft[item.number] ?? item.answer ?? "";
              const bad = !isValid(item, value);
              return (
                <tr key={item.number} className="border-t border-[var(--admin-border)]" data-testid="key-row" data-number={item.number} data-answer={item.answer ?? ""}>
                  <td className="px-3 py-1.5 font-semibold">{item.number}</td>
                  <td>{item.teil}</td>
                  <td className="text-[var(--admin-text-muted)]">{item.label}</td>
                  <td className="text-xs text-[var(--admin-text-muted)]">{TYPE_DE[item.type] ?? item.type}</td>
                  <td>
                    <AdminInput className={`h-8 w-16 px-2 text-center font-mono ${bad ? "ring-2 ring-[var(--admin-danger)]" : ""}`} value={value} maxLength={1} disabled={!item.editable} autoComplete="off"
                      aria-label={`Antwort ${item.number}`} aria-invalid={bad} data-testid="key-input"
                      onChange={(e) => setDraft({ ...draft, [item.number]: e.target.value.replace(/[^A-Za-z]/g, "").slice(0, 1) })} />
                  </td>
                  <td className="max-w-[18rem] truncate text-xs">{item.option_text ?? <span className="text-[var(--admin-warning)]">—</span>}</td>
                  <td className="text-xs text-[var(--admin-text-muted)]">{item.source ? SOURCE_DE[item.source] : <span className="text-[var(--admin-warning)]">fehlt</span>}</td>
                </tr>
              );
            })}
            {!table.items.length && <tr><td colSpan={7} className="p-6 text-center text-[var(--admin-text-muted)]">Dieser Teil hat keine Fragen.</td></tr>}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <AdminButton onClick={() => void save()} disabled={busy || !changed.length} data-testid="keys-save"><Save size={14} /> Änderungen speichern{changed.length ? ` (${changed.length})` : ""}</AdminButton>
        {message && <p role="status" className={`text-sm ${message.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="keys-message">{message.text}</p>}
      </div>

      <div className="space-y-2 rounded-lg bg-[var(--admin-hover)] p-3">
        <AdminLabel htmlFor="keys-import">Import: Antworten als Liste einfügen</AdminLabel>
        <AdminTextarea id="keys-import" rows={4} value={importText} placeholder="1-b, 2-b, 3-b, 4-a, 5-a …" onChange={(e) => { setImportText(e.target.value); setChecked(null); }} data-testid="keys-import-text" />
        <div className="flex flex-wrap items-center gap-2">
          <AdminButton size="sm" variant="secondary" onClick={() => void check()} disabled={busy || !importText.trim()} data-testid="keys-import-check"><FileInput size={13} /> Prüfen</AdminButton>
          <AdminButton size="sm" onClick={() => void apply()} disabled={busy || !checked?.ok} data-testid="keys-import-apply">Übernehmen</AdminButton>
        </div>
        {checked && (
          <div className="text-xs" data-testid="keys-import-result" data-ok={checked.ok ? "1" : "0"}>
            <p className={checked.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}>
              {checked.applied ? "Übernommen: " : checked.ok ? "In Ordnung: " : "Nicht in Ordnung: "}{checked.given} Antworten für {checked.expected} Fragen.
            </p>
            {checked.errors.length > 0 && <ul className="mt-1 list-disc pl-5 text-[var(--admin-danger)]">{checked.errors.slice(0, 8).map((e, i) => <li key={i}>{e.message}</li>)}{checked.errors.length > 8 && <li>… +{checked.errors.length - 8}</li>}</ul>}
          </div>
        )}
      </div>

      <div className="text-xs" data-testid="keys-readiness" data-ready={r.ready ? "1" : "0"}>
        {r.ready ? <p className="text-[var(--admin-success)]">Bereit zur Veröffentlichung: alle Lösungen und alle Hören-Audios sind vorhanden.</p> : (
          <div className="space-y-0.5 text-[var(--admin-text-muted)]">
            <p className="font-semibold text-[var(--admin-warning)]">Noch nicht veröffentlichbar:</p>
            {r.missing_keys.length > 0 && <p>{r.missing_keys.length} Fragen ohne Lösung (z. B. {r.missing_keys.slice(0, 3).join(", ")}).</p>}
            {r.missing_audio.length > 0 && <p>{r.missing_audio.length} Hören-Teile ohne Audio ({r.missing_audio.slice(0, 3).join(", ")}{r.missing_audio.length > 3 ? " …" : ""}).</p>}
            {r.missing_sections.length > 0 && <p>Unvollständig: {r.missing_sections.join("; ")}.</p>}
          </div>
        )}
      </div>
    </div>
  );
}
