"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Pencil } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import MultilevelAnswerKeys from "@/features/admin/components/mock-exam/multilevel-answer-keys";
import { ScoringSettingsCard, SectionScoring } from "@/features/admin/components/mock-exam/multilevel-scoring-admin";
import { useCrudList } from "@/features/admin/hooks/use-crud";
import { mockExamLevelsApi, mockExamModelTestsApi, mockExamProvidersApi } from "@/features/admin/services/mock-exam-service";
import {
  getAdminAttempt,
  getAdminAttempts,
  getStaffRecording,
  getStatistics,
} from "@/features/vorbereitung/services/multilevel-exam-service";
import type { ExamSection } from "@/features/vorbereitung/types/multilevel-exam.types";

const SECTION_DE: Record<ExamSection, string> = { LESEN: "Lesen", HOEREN: "Hören", SCHREIBEN: "Schreiben", SPRECHEN: "Sprechen" };
const LEVEL_DE: Record<string, string> = { NICHT_BESTANDEN: "Nicht bestanden", UNGEKLAERT: "Ungeklärt", PENDING: "Bewertung ausstehend" };
const level = (v: string | null | undefined) => (v ? LEVEL_DE[v] ?? v : "—");

// Admin → Vorbereitung → National Zertifikat → Multilevel B1–C1: Modelltests, statistics, scoring settings (tables, bands, overall rule —
// Super Admin), all attempts with the AI grading of Schreiben / Sprechen and the Super Admin override of any section (reason + history).
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

      {sorted.length > 0 && <MultilevelAnswerKeys tests={sorted.map((t) => ({ id: t.id, title: t.title, status: t.status }))} />}

      <div className="grid gap-6 lg:grid-cols-2">
        <StatisticsCard />
        <ScoringSettingsCard />
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
                  {(Object.keys(SECTION_DE) as ExamSection[]).map((k) => <td key={k}>{r.sections[k]?.no_key ? "ohne Lösung" : r.sections[k]?.score ?? "—"}</td>)}
                  <td>{r.total_score ?? "—"} / {r.max_score ?? 300}</td>
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
        {new Date(d.started_at).toLocaleString("de-DE")} · Status {d.status} · Gesamt {d.total_score ?? "—"} / {d.max_score ?? 300} · Niveau {level(d.result_level)}
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
            <SectionScoring key={`${s.type}-${s.score}-${s.override_score}-${s.ai_status}`} attemptId={d.attempt_id} s={s}
              onChanged={async () => {
                await queryClient.invalidateQueries({ queryKey: ["multilevel-admin-attempt", attemptId] });
                await queryClient.invalidateQueries({ queryKey: ["multilevel-admin-attempts"] });
                await queryClient.invalidateQueries({ queryKey: ["multilevel-statistics"] });
              }} />
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
