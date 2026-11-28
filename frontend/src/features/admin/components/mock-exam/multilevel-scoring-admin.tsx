"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, History, RotateCw } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { formatGaps, formatSchreibenTable, lesenTableProblems, parseSchreibenTable } from "@/features/vorbereitung/lib/multilevel-scoring";
import { getScoringSettings, gradeSection, putScoringSettings, reevaluateSection } from "@/features/vorbereitung/services/multilevel-exam-service";
import type { AdminResultSection, AiEvaluationView, ExamSection, ScoringBands, ScoringSettings } from "@/features/vorbereitung/types/multilevel-exam.types";

const RULES: Record<string, string> = {
  UNCONFIRMED: "Nicht bestätigt — Gesamtniveau bleibt „Ungeklärt“ (Standard)",
  AVERAGE: "Durchschnitt der vier Teile (gleiche Punktbereiche)",
  LOWEST: "Niedrigstes Teilniveau",
};
const SOURCE_DE: Record<string, string> = { AUTO: "Tabelle", AI: "KI", MANUAL: "Super Admin" };
const AI_DE: Record<string, string> = {
  PENDING: "KI-Bewertung wartet", RUNNING: "KI bewertet gerade", DONE: "KI-Bewertung fertig", FAILED: "KI-Bewertung fehlgeschlagen",
  NEEDS_ADMIN: "Rohpunkte außerhalb der Tabelle — bitte von Hand bewerten oder Tabelle ergänzen",
};
const muted = "text-xs text-[var(--admin-text-muted)]";

// ------------------------------------------------------------------ settings

/** Super Admin: overall rule, level bands, Lesen / Hören table, official Schreiben table (owner 2026-11-28). Saving recomputes stored results. */
export function ScoringSettingsCard() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["multilevel-settings"], queryFn: getScoringSettings });
  if (!data) return <AdminCard><p className={muted}>Bewertungsregeln laden…</p></AdminCard>;
  return <SettingsForm key={JSON.stringify([data.bands, data.lesen_table, data.schreiben_table, data.overall_rule])} data={data}
    onSaved={async () => {
      await queryClient.invalidateQueries({ queryKey: ["multilevel-settings"] });
      await queryClient.invalidateQueries({ queryKey: ["multilevel-admin-attempts"] });
      await queryClient.invalidateQueries({ queryKey: ["multilevel-admin-attempt"] });
    }} />;
}

function SettingsForm({ data, onSaved }: { data: ScoringSettings; onSaved: () => Promise<void> }) {
  const [rule, setRule] = useState(data.overall_rule);
  const [bands, setBands] = useState<ScoringBands>(data.bands);
  const [lesen, setLesen] = useState<number[]>(data.lesen_table);
  const [schreiben, setSchreiben] = useState(formatSchreibenTable(data.schreiben_table));
  const [message, setMessage] = useState<string | null>(null);
  const parsed = parseSchreibenTable(schreiben);
  const lesenProblem = lesenTableProblems(lesen);

  async function save() {
    setMessage(null);
    if (lesenProblem || parsed.errors.length) {
      setMessage(lesenProblem ?? `Schreiben-Tabelle: Zeile ${parsed.errors.join(", ")} nicht lesbar.`);
      return;
    }
    try {
      const out = await putScoringSettings({ overall_rule: rule, bands, lesen_table: lesen, schreiben_table: parsed.rows });
      setMessage(`Gespeichert. ${out.results_changed ?? 0} gespeicherte Ergebnisse neu berechnet.`);
      await onSaved();
    } catch (err) {
      setMessage(apiErrorMessage(err, "Speichern fehlgeschlagen (nur Super Admin)."));
    }
  }

  return (
    <AdminCard>
      <h2 className="mb-1 text-sm font-semibold text-[var(--admin-text-primary)]">Bewertungsregeln</h2>
      <p className={`mb-3 ${muted}`}>
        Je Teil 0–75 Punkte, gesamt 0–300. Lesen / Hören: richtige Antworten auf der 35er-Skala (Hören 30 → × 35 / 30) → Tabelle. Schreiben: KI
        bewertet Teil 1.1 (0–5), 1.2 (0–7), 2 (0–24) → offizielle 36 → 75-Tabelle. Sprechen: KI, sechs Kriterien je Teil (0–5), linear auf 75.
      </p>
      <div className="space-y-4" data-testid="ml-scoring-settings">
        <div>
          <AdminLabel>Gesamtniveau</AdminLabel>
          <AdminSelect value={rule} onChange={(e) => setRule(e.target.value as ScoringSettings["overall_rule"])} data-testid="setting-overall">
            {Object.entries(RULES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </AdminSelect>
        </div>
        <div>
          <AdminLabel>Niveau-Grenzen (ab Punkten, Standard B1 38 · B2 51 · C1 65)</AdminLabel>
          <div className="grid grid-cols-3 gap-2">
            {(["B1", "B2", "C1"] as const).map((k) => (
              <label key={k} className="text-xs text-[var(--admin-text-muted)]">{k}
                <AdminInput type="number" min={1} max={75} value={bands[k]} data-testid={`setting-band-${k}`}
                  onChange={(e) => setBands({ ...bands, [k]: Number(e.target.value) })} /></label>
            ))}
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between gap-2">
            <AdminLabel>Lesen / Hören: Punkte je Anzahl richtiger Antworten (0–35)</AdminLabel>
            {data.defaults && <AdminButton size="sm" variant="secondary" onClick={() => setLesen(data.defaults!.lesen_table)}>Standard</AdminButton>}
          </div>
          <div className="grid grid-cols-6 gap-1 sm:grid-cols-9" data-testid="setting-lesen-table">
            {lesen.map((v, i) => (
              <label key={i} className="text-[10px] text-[var(--admin-text-muted)]">{i}
                <AdminInput type="number" min={0} max={75} value={v} className="h-8 px-1 text-xs"
                  onChange={(e) => setLesen(lesen.map((x, j) => (j === i ? Number(e.target.value) : x)))} /></label>
            ))}
          </div>
          {lesenProblem && <p className="mt-1 text-xs text-[var(--admin-danger)]">{lesenProblem}</p>}
        </div>
        <div>
          <div className="flex items-center justify-between gap-2">
            <AdminLabel>Schreiben: offizielle Tabelle (Rohpunkte 0–36 → 0–75), eine Zeile „von–bis = Punkte“</AdminLabel>
            {data.defaults && <AdminButton size="sm" variant="secondary" onClick={() => setSchreiben(formatSchreibenTable(data.defaults!.schreiben_table))}>Standard</AdminButton>}
          </div>
          <AdminTextarea rows={8} value={schreiben} onChange={(e) => setSchreiben(e.target.value)} className="font-mono text-xs" data-testid="setting-schreiben-table" />
          {parsed.errors.length > 0 && <p className="mt-1 text-xs text-[var(--admin-danger)]">Zeile {parsed.errors.join(", ")} nicht lesbar.</p>}
          {(data.schreiben_missing?.length ?? 0) > 0 && (
            <p className="mt-1 flex items-start gap-1 text-xs text-amber-500" data-testid="setting-schreiben-missing">
              <AlertTriangle size={13} className="mt-0.5 shrink-0" />
              Fehlt in der Tabelle (im Bild nicht lesbar, nicht erfunden): {formatGaps(data.schreiben_missing)}. Solche Rohpunkte bewertet der Super Admin von Hand.
            </p>
          )}
        </div>
        <AdminButton onClick={() => void save()} size="sm" data-testid="setting-save">Speichern</AdminButton>
        {message && <p className={muted} data-testid="setting-message">{message}</p>}
      </div>
    </AdminCard>
  );
}

// ------------------------------------------------------------------ one section

function EvaluationView({ ev }: { ev: AiEvaluationView }) {
  return (
    <div className="mt-2 space-y-2 rounded-md bg-white/[0.02] p-2 text-xs" data-testid="ml-ai-evaluation">
      <p className="font-semibold text-[var(--admin-text-primary)]">
        KI: {ev.raw} / {ev.raw_max} Rohpunkte → {ev.converted ?? "keine Umrechnung"}{ev.converted != null ? " / 75" : ""}
      </p>
      {ev.summary && <p className="text-[var(--admin-text-primary)]">{ev.summary}</p>}
      {ev.teile.map((t) => (
        <div key={t.teil} className="rounded p-2 ring-1 ring-[var(--admin-border)]">
          <p className="font-semibold text-[var(--admin-text-primary)]">{t.title}: {t.score} / {t.max}</p>
          {t.explanation && <p className="text-[var(--admin-text-muted)]">{t.explanation}</p>}
          {t.criteria?.map((c, i) => (
            <p key={i} className="text-[var(--admin-text-muted)]">• {c.name}{c.score != null ? ` ${c.score}/${c.max}` : c.status === "not_assessed" ? " (nicht bewertet)" : ""}: {c.comment}</p>
          ))}
          {(t.mistakes?.length ?? 0) > 0 && (
            <ul className="mt-1 text-[var(--admin-text-muted)]">
              {t.mistakes!.map((m, i) => <li key={i}>✗ „{m.original}“ → „{m.correction}“{m.explanation ? ` — ${m.explanation}` : ""}</li>)}
            </ul>
          )}
          {t.transcript && <p className="mt-1 italic text-[var(--admin-text-muted)]">Transkript: {t.transcript}</p>}
        </div>
      ))}
      {(ev.recommendations?.length ?? 0) > 0 && <p className="text-[var(--admin-text-muted)]">Empfehlungen: {ev.recommendations!.join(" · ")}</p>}
      {(ev.limitations?.length ?? 0) > 0 && <p className="text-amber-500">{ev.limitations!.join(" ")}</p>}
    </div>
  );
}

/** Score trail + Super Admin actions of one section: rule / AI score vs override, AI explanation, override (reason required), clear, re-run, history. */
export function SectionScoring({ attemptId, s, onChanged }: { attemptId: string; s: AdminResultSection; onChanged: () => Promise<void> }) {
  const [score, setScore] = useState(s.override_score?.toString() ?? s.score?.toString() ?? "");
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const closed = s.status !== "OPEN" && s.status !== "NOT_STARTED";
  const ai = s.type === "SCHREIBEN" || s.type === "SPRECHEN";

  async function run(fn: () => Promise<unknown>, ok: string) {
    setMsg(null);
    try {
      await fn();
      setMsg(ok);
      setReason("");
      await onChanged();
    } catch (err) {
      setMsg(apiErrorMessage(err, "Fehlgeschlagen (nur Super Admin)."));
    }
  }

  function save() {
    const value = Number(score);
    if (!Number.isInteger(value) || value < 0 || value > 75) return setMsg("Punkte: ganze Zahl 0–75.");
    if (reason.trim().length < 3) return setMsg("Bitte einen Grund angeben.");
    void run(() => gradeSection(attemptId, s.type as ExamSection, value, reason.trim()), "Gespeichert — die Änderung steht im Verlauf.");
  }

  return (
    <div className="mt-3 space-y-2 border-t border-[var(--admin-border)] pt-3" data-testid={`grade-${s.type}`}>
      <p className={muted} data-testid={`ml-source-${s.type}`}>
        Quelle: {s.score_source ? SOURCE_DE[s.score_source] : "—"}
        {s.auto_score != null && ` · Tabelle/KI: ${s.auto_score}`}
        {s.override_score != null && ` · Super Admin: ${s.override_score}`}
        {s.auto_score != null && s.override_score != null && ` (Abweichung ${s.override_score - s.auto_score > 0 ? "+" : ""}${s.override_score - s.auto_score})`}
      </p>
      {ai && s.ai_status && (
        <p className={`text-xs ${s.ai_status === "FAILED" || s.ai_status === "NEEDS_ADMIN" ? "text-amber-500" : "text-[var(--admin-text-muted)]"}`} data-testid={`ml-ai-status-${s.type}`}>
          {AI_DE[s.ai_status] ?? s.ai_status}{s.ai_runs ? ` · Läufe: ${s.ai_runs}` : ""}
        </p>
      )}
      {s.evaluation_full && <EvaluationView ev={s.evaluation_full} />}
      {closed && (
        <>
          <div className="flex flex-wrap items-end gap-2">
            <div className="w-28">
              <AdminLabel>Punkte (0–75)</AdminLabel>
              <AdminInput type="number" min={0} max={75} value={score} onChange={(e) => setScore(e.target.value)} data-testid={`override-score-${s.type}`} />
            </div>
            <div className="min-w-[12rem] flex-1">
              <AdminLabel>Grund (Pflicht)</AdminLabel>
              <AdminInput value={reason} maxLength={1000} onChange={(e) => setReason(e.target.value)} placeholder="z. B. Zweitkorrektur" data-testid={`override-reason-${s.type}`} />
            </div>
            <AdminButton size="sm" onClick={save} data-testid={`override-save-${s.type}`}>Punkte setzen</AdminButton>
            {s.override_score != null && (
              <AdminButton size="sm" variant="secondary" data-testid={`override-clear-${s.type}`}
                onClick={() => (reason.trim().length < 3 ? setMsg("Bitte einen Grund angeben.") :
                  void run(() => gradeSection(attemptId, s.type as ExamSection, null, reason.trim()), "Zurückgenommen — Tabelle/KI zählt wieder."))}>
                Zurücknehmen
              </AdminButton>
            )}
            {ai && (
              <AdminButton size="sm" variant="secondary" data-testid={`reevaluate-${s.type}`}
                onClick={() => void run(() => reevaluateSection(attemptId, s.type as ExamSection), "KI bewertet neu — eine Handbewertung bleibt bestehen.")}>
                <RotateCw size={13} /> KI neu bewerten
              </AdminButton>
            )}
          </div>
          {msg && <p className={muted} data-testid={`override-msg-${s.type}`}>{msg}</p>}
        </>
      )}
      {(s.history?.length ?? 0) > 0 && (
        <div>
          <button type="button" onClick={() => setShowHistory(!showHistory)} className="flex items-center gap-1 text-xs font-semibold text-[var(--admin-primary)]" data-testid={`history-toggle-${s.type}`}>
            <History size={13} /> Verlauf ({s.history!.length})
          </button>
          {showHistory && (
            <ul className="mt-1 space-y-1 text-xs text-[var(--admin-text-muted)]" data-testid={`history-${s.type}`}>
              {s.history!.map((h) => (
                <li key={h.id}>
                  {new Date(h.created_at).toLocaleString("de-DE")} ·{" "}
                  {h.source === "AI"
                    ? (h.status === "FAILED" ? `KI fehlgeschlagen (${h.error ?? "?"})` : `KI: ${h.raw ?? "?"} / ${h.raw_max ?? "?"} → ${h.score ?? "keine Umrechnung"}`)
                    : `${h.actor ?? "Admin"}: ${h.old_score ?? "—"} → ${h.cleared ? `zurückgenommen (${h.new_score ?? "—"})` : h.new_score} · „${h.reason ?? ""}“`}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
