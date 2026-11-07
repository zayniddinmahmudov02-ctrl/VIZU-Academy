"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Pencil } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminPageHeader, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import { useCrudList } from "@/features/admin/hooks/use-crud";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { mockExamLevelsApi, mockExamModelTestsApi, mockExamProvidersApi } from "@/features/admin/services/mock-exam-service";
import {
  getAdminAttempt,
  getAdminAttempts,
  getScoringSettings,
  getStaffRecording,
  getStatistics,
  gradeSection,
  putScoringSettings,
} from "@/features/vorbereitung/services/multilevel-exam-service";
import type { AdminAttemptDetail, ExamSection, ScoringSettings } from "@/features/vorbereitung/types/multilevel-exam.types";

const SECTION_DE: Record<ExamSection, string> = { LESEN: "Lesen", HOEREN: "Hören", SCHREIBEN: "Schreiben", SPRECHEN: "Sprechen" };
const LEVEL_DE: Record<string, string> = { NICHT_BESTANDEN: "Nicht bestanden", UNGEKLAERT: "Ungeklärt", PENDING: "Bewertung ausstehend" };
const level = (v: string | null | undefined) => (v ? LEVEL_DE[v] ?? v : "—");
const RULES: Record<string, string> = {
  UNCONFIRMED: "Nicht bestätigt — Gesamtniveau bleibt „Ungeklärt“ (Standard)",
  AVERAGE: "Durchschnitt der vier Teile (gleiche Punktbereiche)",
  LOWEST: "Niedrigstes Teilniveau",
};
const SCORE_50: Record<string, string> = { UNGEKLAERT: "Ungeklärt (Standard)", B1: "B1", B2: "B2" };

// Admin → Vorbereitung → National Zertifikat → Multilevel B1–C1: Modelltests, statistics, scoring settings (50-point
// rule, overall rule — Super Admin), all attempts and the Schreiben / Sprechen grading (0–75, teachers + admins).
export default function MultilevelAdminPage() {
  const { data: providers } = useCrudList("mock-exam-providers", mockExamProvidersApi);
  const provider = providers?.find((p) => p.code === "NATIONAL");
  const { data: levels } = useCrudList("mock-exam-levels", mockExamLevelsApi, provider ? { provider_id: provider.id } : undefined);
  const level_ = levels?.find((l) => l.title === "Multilevel B1–C1");
  const { data: tests } = useCrudList("mock-exam-model-tests", mockExamModelTestsApi, level_ ? { level_id: level_.id } : undefined);
  const [selected, setSelected] = useState<string | null>(null);

  const sorted = level_ ? [...(tests ?? [])].filter((t) => t.level_id === level_.id).sort((a, b) => a.sort_order - b.sort_order) : [];

  return (
    <div className="space-y-6">
      <AdminPageHeader
        title="Multilevel B1–C1 · National Zertifikat"
        description="Modelltests, Prüfungsergebnisse, Bewertung von Schreiben / Sprechen und Bewertungsregeln. Schüler wählen kein Niveau — das Ergebnis wird automatisch bestimmt."
      />

      <AdminCard>
        <h2 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Modelltests</h2>
        {!level_ && <p className="text-sm text-[var(--admin-text-muted)]">Level „Multilevel B1–C1“ nicht gefunden.</p>}
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {sorted.map((t) => (
            <div key={t.id} className="flex items-center justify-between gap-2 rounded-lg p-3 ring-1 ring-[var(--admin-border)]">
              <div>
                <p className="text-sm font-semibold text-[var(--admin-text-primary)]">{t.title}</p>
                <p className={`text-xs ${t.status === "PUBLISHED" ? "text-[var(--admin-accent)]" : "text-[var(--admin-text-muted)]"}`}>
                  {t.status === "PUBLISHED" ? "Veröffentlicht" : t.status === "DRAFT" ? "Entwurf" : t.status}
                </p>
              </div>
              <div className="flex gap-1">
                <Link href={`/admin/mock-exams/${provider!.id}/${level_!.id}/${t.id}`} title="Bearbeiten"
                  className="flex h-8 w-8 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-hover)]"><Pencil size={14} /></Link>
                <Link href={`/admin/mock-exams/${provider!.id}/${level_!.id}/${t.id}/preview`} title="Vorschau"
                  className="flex h-8 w-8 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-hover)]"><Eye size={14} /></Link>
              </div>
            </div>
          ))}
        </div>
      </AdminCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <StatisticsCard />
        <SettingsCard />
      </div>

      <AttemptsCard onSelect={setSelected} selected={selected} />
      {selected && <AttemptDetailCard attemptId={selected} />}
    </div>
  );
}

function StatisticsCard() {
  const { data: s } = useQuery({ queryKey: ["multilevel-statistics"], queryFn: getStatistics });
  return (
    <AdminCard>
      <h2 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Statistik</h2>
      {s && (
        <div className="space-y-3 text-sm text-[var(--admin-text-primary)]">
          <p>Versuche: {s.attempts} · beendet: {s.finished} · vollständig bewertet: {s.graded}</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {(Object.keys(SECTION_DE) as ExamSection[]).map((k) => (
              <div key={k} className="rounded-lg p-2 ring-1 ring-[var(--admin-border)]">
                <p className="text-xs text-[var(--admin-text-muted)]">{SECTION_DE[k]}</p>
                <p className="font-semibold">{s.sections[k]?.average ?? "—"} / 75</p>
                <p className="text-xs text-[var(--admin-text-muted)]">n = {s.sections[k]?.count ?? 0}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-[var(--admin-text-muted)]">
            Niveaus: {Object.entries(s.levels).map(([k, v]) => `${level(k)} ${v}`).join(" · ") || "—"}
          </p>
          {s.tests.length > 0 && (
            <ul className="text-xs text-[var(--admin-text-muted)]">
              {s.tests.map((t) => <li key={t.model_test_id}>{t.title}: {t.attempts} Versuche, Ø {t.average_total ?? "—"} / 300</li>)}
            </ul>
          )}
        </div>
      )}
    </AdminCard>
  );
}

function SettingsCard() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["multilevel-settings"], queryFn: getScoringSettings });
  const [edited, setForm] = useState<Pick<ScoringSettings, "score_50" | "overall_rule"> | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const form = edited ?? (data ? { score_50: data.score_50, overall_rule: data.overall_rule } : null);

  async function save() {
    if (!form) return;
    setMessage(null);
    try {
      const out = await putScoringSettings(form);
      setMessage(`Gespeichert. ${out.results_changed ?? 0} gespeicherte Ergebnisse neu berechnet.`);
      await queryClient.invalidateQueries({ queryKey: ["multilevel-settings"] });
      await queryClient.invalidateQueries({ queryKey: ["multilevel-admin-attempts"] });
    } catch (err) {
      setMessage(apiErrorMessage(err, "Speichern fehlgeschlagen (nur Super Admin)."));
    }
  }

  return (
    <AdminCard>
      <h2 className="mb-1 text-sm font-semibold text-[var(--admin-text-primary)]">Bewertungsregeln</h2>
      <p className="mb-3 text-xs text-[var(--admin-text-muted)]">
        Je Teil 0–75 Punkte: 0–38 Nicht bestanden · 39–49 B1 · 50 = Einstellung · 51–64 B2 · 65–75 C1. Gesamt 0–300.
        Lesen/Hören: richtige / alle Fragen × 75 (gerundet). Ohne offizielle Regel bleibt das Gesamtniveau „Ungeklärt“.
      </p>
      {form && (
        <div className="space-y-3">
          <div>
            <AdminLabel>50 Punkte</AdminLabel>
            <AdminSelect value={form.score_50} onChange={(e) => setForm({ ...form, score_50: e.target.value as ScoringSettings["score_50"] })} data-testid="setting-score-50">
              {Object.entries(SCORE_50).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </AdminSelect>
          </div>
          <div>
            <AdminLabel>Gesamtniveau</AdminLabel>
            <AdminSelect value={form.overall_rule} onChange={(e) => setForm({ ...form, overall_rule: e.target.value as ScoringSettings["overall_rule"] })} data-testid="setting-overall">
              {Object.entries(RULES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </AdminSelect>
          </div>
          <AdminButton onClick={() => void save()} size="sm">Speichern</AdminButton>
          {message && <p className="text-xs text-[var(--admin-text-muted)]">{message}</p>}
        </div>
      )}
    </AdminCard>
  );
}

function AttemptsCard({ onSelect, selected }: { onSelect: (id: string) => void; selected: string | null }) {
  const [status, setStatus] = useState("");
  const { data: rows = [] } = useQuery({
    queryKey: ["multilevel-admin-attempts", status],
    queryFn: () => getAdminAttempts(status ? { status } : {}),
  });
  return (
    <AdminCard>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-[var(--admin-text-primary)]">Versuche</h2>
        <div className="w-56">
          <AdminSelect value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Alle</option>
            <option value="SUBMITTED">Bewertung ausstehend</option>
            <option value="GRADED">Bewertet</option>
            <option value="IN_PROGRESS">Läuft</option>
          </AdminSelect>
        </div>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Versuche.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm text-[var(--admin-text-primary)]">
            <thead className="text-xs text-[var(--admin-text-muted)]">
              <tr><th className="py-2">Schüler</th><th>Test</th><th>Datum</th>{Object.values(SECTION_DE).map((s) => <th key={s}>{s}</th>)}<th>Gesamt</th><th>Niveau</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.attempt_id} onClick={() => onSelect(r.attempt_id)}
                  className={`cursor-pointer border-t border-[var(--admin-border)] hover:bg-[var(--admin-hover)] ${selected === r.attempt_id ? "bg-[var(--admin-hover)]" : ""}`}>
                  <td className="py-2">{r.username ?? r.email}</td>
                  <td>{r.title}</td>
                  <td>{new Date(r.started_at).toLocaleDateString("de-DE")}</td>
                  {(Object.keys(SECTION_DE) as ExamSection[]).map((k) => <td key={k}>{r.sections[k]?.score ?? "—"}</td>)}
                  <td>{r.total_score ?? "—"} / 300</td>
                  <td>{r.status === "IN_PROGRESS" ? "läuft" : level(r.result_level)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AdminCard>
  );
}

function AttemptDetailCard({ attemptId }: { attemptId: string }) {
  const queryClient = useQueryClient();
  const { data: d } = useQuery({ queryKey: ["multilevel-admin-attempt", attemptId], queryFn: () => getAdminAttempt(attemptId) });
  if (!d) return null;
  return (
    <AdminCard>
      <h2 className="text-sm font-semibold text-[var(--admin-text-primary)]">{d.username ?? d.email} · {d.title}</h2>
      <p className="mb-4 text-xs text-[var(--admin-text-muted)]">
        {new Date(d.started_at).toLocaleString("de-DE")} · Status {d.status} · Gesamt {d.total_score ?? "—"} / 300 · Niveau {level(d.result_level)}
      </p>
      <div className="grid gap-4 lg:grid-cols-2">
        {d.sections.map((s) => (
          <div key={s.type} className="rounded-lg p-3 ring-1 ring-[var(--admin-border)]">
            <p className="text-sm font-semibold text-[var(--admin-text-primary)]">{SECTION_DE[s.type]}: {s.score ?? "—"} / 75 · {level(s.level)}</p>
            <p className="text-xs text-[var(--admin-text-muted)]">{s.status}{s.raw_max ? ` · ${s.raw_points} / ${s.raw_max} richtig` : ""}</p>
            {s.type === "SCHREIBEN" && d.writings.map((w, i) => (
              <div key={i} className="mt-2 rounded-md bg-white/[0.02] p-2 text-xs">
                <p className="font-semibold text-[var(--admin-text-primary)]">{w.teil} · {w.word_count} Wörter{w.word_limit ? ` (Ziel ~${w.word_limit})` : ""}</p>
                {w.rubric && <p className="mt-1 whitespace-pre-line text-[var(--admin-text-muted)]">Kriterien: {w.rubric}</p>}
                <p className="mt-1 whitespace-pre-line text-[var(--admin-text-primary)]">{w.answer_text}</p>
              </div>
            ))}
            {s.type === "SPRECHEN" && d.recordings.map((r) => <RecordingRow key={r.submission_id} id={r.submission_id} label={r.teil} />)}
            {(s.type === "SCHREIBEN" || s.type === "SPRECHEN") && s.status !== "OPEN" && s.status !== "NOT_STARTED" && (
              <GradeForm d={d} section={s.type} current={s.score} feedback={s.feedback}
                onDone={async () => {
                  await queryClient.invalidateQueries({ queryKey: ["multilevel-admin-attempt", attemptId] });
                  await queryClient.invalidateQueries({ queryKey: ["multilevel-admin-attempts"] });
                  await queryClient.invalidateQueries({ queryKey: ["multilevel-statistics"] });
                }} />
            )}
          </div>
        ))}
      </div>
    </AdminCard>
  );
}

function RecordingRow({ id, label }: { id: string; label: string }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => () => {
    if (url) URL.revokeObjectURL(url);
  }, [url]);
  return (
    <div className="mt-2 text-xs">
      <p className="font-semibold text-[var(--admin-text-primary)]">{label}</p>
      {url ? <audio controls src={url} className="mt-1 w-full" /> : (
        <AdminButton size="sm" variant="secondary" className="mt-1"
          onClick={async () => setUrl(URL.createObjectURL(await getStaffRecording(id)))}>Aufnahme laden</AdminButton>
      )}
    </div>
  );
}

function GradeForm({ d, section, current, feedback, onDone }: {
  d: AdminAttemptDetail; section: ExamSection; current: number | null; feedback: string | null; onDone: () => Promise<void>;
}) {
  const [score, setScore] = useState(current?.toString() ?? "");
  const [text, setText] = useState(feedback ?? "");
  const [msg, setMsg] = useState<string | null>(null);
  async function save() {
    const value = Number(score);
    if (!Number.isInteger(value) || value < 0 || value > 75) {
      setMsg("Punkte: ganze Zahl 0–75.");
      return;
    }
    try {
      await gradeSection(d.attempt_id, section, value, text || null);
      setMsg("Gespeichert.");
      await onDone();
    } catch (err) {
      setMsg(apiErrorMessage(err, "Speichern fehlgeschlagen."));
    }
  }
  return (
    <div className="mt-3 space-y-2 border-t border-[var(--admin-border)] pt-3" data-testid={`grade-${section}`}>
      <div className="flex items-end gap-2">
        <div className="w-28">
          <AdminLabel>Punkte (0–75)</AdminLabel>
          <AdminInput type="number" min={0} max={75} value={score} onChange={(e) => setScore(e.target.value)} />
        </div>
        <AdminButton size="sm" onClick={() => void save()}>Bewerten</AdminButton>
      </div>
      <AdminTextarea rows={2} placeholder="Rückmeldung (optional)" value={text} onChange={(e) => setText(e.target.value)} />
      {msg && <p className="text-xs text-[var(--admin-text-muted)]">{msg}</p>}
    </div>
  );
}
