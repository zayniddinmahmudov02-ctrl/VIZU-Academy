"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Download, Loader2, Search, Trophy } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  downloadVizuMultilevelAttemptCertificatePdf,
  listVizuMultilevelStudents,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type {
  VizuMultilevelStudentAttempt,
  VizuMultilevelStudentRow,
  VizuMultilevelStudentSort,
} from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";

const PAGE_SIZE = 20;
const SORTS: { value: VizuMultilevelStudentSort; label: string }[] = [
  { value: "best_score", label: "Bestes Ergebnis" },
  { value: "level", label: "Niveau" },
  { value: "attempts", label: "Versuche" },
  { value: "date", label: "Datum" },
];

function levelText(level: string | null): string {
  if (!level) return "—";
  return level === "BELOW_A1" ? "unter A1" : level;
}

function scoreText(score: number | null): string {
  return score === null ? "—" : `${score} / 100`;
}

function dateText(value: string | null): string {
  return value ? new Date(value).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" }) : "—";
}

function lastAttemptText(row: VizuMultilevelStudentRow): string {
  if (!row.last_attempt_number) return "—";
  if (row.last_attempt_status === "IN_PROGRESS") return `Versuch ${row.last_attempt_number} · läuft`;
  return `Versuch ${row.last_attempt_number} · ${dateText(row.last_attempt_date)}`;
}

/** "Studenten": one row per student — Bestes Ergebnis (highest Gesamtergebnis
 * over ALL final attempts, not just the last) is the headline. Sortable by
 * best score (default, descending), level, attempts and date. */
export default function VizuMultilevelStudentsTab() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<VizuMultilevelStudentSort>("best_score");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [selected, setSelected] = useState<VizuMultilevelStudentRow | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["vizu-multilevel-admin-students", page, search, sort, order],
    queryFn: () => listVizuMultilevelStudents({ page, page_size: PAGE_SIZE, search: search || undefined, sort, order }),
  });

  return (
    <div data-testid="admin-students">
      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
          <AdminInput
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Suche nach Name oder E-Mail..."
            className="pl-9"
          />
        </div>
        <AdminSelect
          value={sort}
          onChange={(e) => {
            setSort(e.target.value as VizuMultilevelStudentSort);
            setPage(1);
          }}
          className="w-full sm:w-64"
          aria-label="Sortieren nach"
          data-testid="students-sort"
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              Sortieren: {s.label}
            </option>
          ))}
        </AdminSelect>
        <AdminButton
          variant="secondary"
          onClick={() => {
            setOrder((o) => (o === "desc" ? "asc" : "desc"));
            setPage(1);
          }}
          aria-label={order === "desc" ? "Absteigend" : "Aufsteigend"}
          data-testid="students-order"
        >
          {order === "desc" ? <ArrowDown size={14} /> : <ArrowUp size={14} />}
          {order === "desc" ? "Absteigend" : "Aufsteigend"}
        </AdminButton>
      </div>

      {isLoading && <Loader2 size={18} className="animate-spin text-[var(--admin-primary)]" />}
      {data && data.items.length === 0 && <p className="py-8 text-center text-sm text-[var(--admin-text-muted)]">Keine Studenten gefunden.</p>}

      {data && data.items.length > 0 && (
        <>
          {/* Desktop: table */}
          <div className="hidden overflow-x-auto rounded-xl ring-1 ring-[var(--admin-border)] md:block">
            <table className="w-full text-left text-sm">
              <thead className="bg-[var(--admin-surface-muted,transparent)] text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Versuche</th>
                  <th className="px-4 py-3">Bestes Ergebnis</th>
                  <th className="px-4 py-3">Bestes Niveau</th>
                  <th className="px-4 py-3">Letzter Versuch</th>
                  <th className="px-4 py-3">Letztes Ergebnis</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--admin-border)]">
                {data.items.map((row) => (
                  <tr
                    key={row.user_id}
                    onClick={() => setSelected(row)}
                    className="cursor-pointer transition-colors hover:bg-[var(--admin-hover,rgba(0,0,0,0.03))]"
                    data-testid="student-row"
                  >
                    <td className="px-4 py-3">
                      <p className="font-semibold text-[var(--admin-text-primary)]">{row.student_name}</p>
                      <p className="text-xs text-[var(--admin-text-muted)]">{row.email}</p>
                    </td>
                    <td className="px-4 py-3 tabular-nums text-[var(--admin-text-secondary)]">
                      {row.attempts_used} / {row.max_attempts}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5 font-bold tabular-nums text-[var(--admin-text-primary)]">
                        {row.best_score !== null && <Trophy size={14} className="text-amber-500" />}
                        {scoreText(row.best_score)}
                      </span>
                      {row.best_attempt_number && (
                        <p className="text-xs text-[var(--admin-text-muted)]">Versuch {row.best_attempt_number}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 font-semibold text-[var(--admin-text-primary)]">{levelText(row.best_level)}</td>
                    <td className="px-4 py-3 text-[var(--admin-text-secondary)]">{lastAttemptText(row)}</td>
                    <td className="px-4 py-3 tabular-nums text-[var(--admin-text-secondary)]">
                      {scoreText(row.last_attempt_score)}
                      {row.last_attempt_level ? ` · ${levelText(row.last_attempt_level)}` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile: cards */}
          <div className="space-y-3 md:hidden">
            {data.items.map((row) => (
              <button
                key={row.user_id}
                type="button"
                onClick={() => setSelected(row)}
                className="w-full rounded-xl p-4 text-left ring-1 ring-[var(--admin-border)]"
                data-testid="student-card"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-[var(--admin-text-primary)]">{row.student_name}</p>
                    <p className="truncate text-xs text-[var(--admin-text-muted)]">{row.email}</p>
                  </div>
                  <span className="shrink-0 text-xs text-[var(--admin-text-muted)]">
                    Versuche: {row.attempts_used} / {row.max_attempts}
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-xs text-[var(--admin-text-muted)]">Bestes Ergebnis</p>
                    <p className="font-bold text-[var(--admin-text-primary)]">
                      {row.best_score === null ? "—" : `${scoreText(row.best_score)} · ${levelText(row.best_level)}`}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--admin-text-muted)]">Letzter Versuch</p>
                    <p className="font-semibold text-[var(--admin-text-secondary)]">
                      {row.last_attempt_score === null ? "—" : `${scoreText(row.last_attempt_score)} · ${levelText(row.last_attempt_level)}`}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </>
      )}

      {data && data.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
          <span>
            Seite {data.page} von {data.total_pages} ({data.total} Studenten)
          </span>
          <div className="flex gap-2">
            <AdminButton variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft size={14} />
            </AdminButton>
            <AdminButton variant="secondary" size="sm" disabled={page >= data.total_pages} onClick={() => setPage((p) => p + 1)}>
              <ChevronRight size={14} />
            </AdminButton>
          </div>
        </div>
      )}

      <FormDialog
        open={!!selected}
        onOpenChange={(open) => !open && setSelected(null)}
        title={selected?.student_name ?? ""}
        description={selected?.email}
        size="lg"
      >
        {selected && <StudentAttempts row={selected} />}
      </FormDialog>
    </div>
  );
}

function StudentAttempts({ row }: { row: VizuMultilevelStudentRow }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Stat label="Versuche" value={`${row.attempts_used} / ${row.max_attempts}`} />
        <Stat label="Bestes Ergebnis" value={scoreText(row.best_score)} />
        <Stat label="Bestes Niveau" value={levelText(row.best_level)} />
        <Stat label="Bester Versuch" value={row.best_attempt_number ? String(row.best_attempt_number) : "—"} />
      </div>
      <div className="overflow-hidden rounded-xl ring-1 ring-[var(--admin-border)]">
        <table className="w-full text-left text-sm">
          <tbody className="divide-y divide-[var(--admin-border)]">
            {row.attempts.map((a) => (
              <AttemptLine key={a.id} attempt={a} isBest={a.id === row.best_attempt_id} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg p-3 ring-1 ring-[var(--admin-border)]">
      <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
      <p className="font-bold text-[var(--admin-text-primary)]">{value}</p>
    </div>
  );
}

function AttemptLine({ attempt, isBest }: { attempt: VizuMultilevelStudentAttempt; isBest: boolean }) {
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);

  async function download() {
    setPending(true);
    setFailed(false);
    try {
      await downloadVizuMultilevelAttemptCertificatePdf(attempt.id);
    } catch {
      setFailed(true);
    } finally {
      setPending(false);
    }
  }

  const status =
    attempt.status === "IN_PROGRESS"
      ? "läuft"
      : attempt.result_score === null
        ? "Auswertung läuft"
        : `${attempt.result_score} / 100 · ${levelText(attempt.result_level)}`;

  return (
    <tr data-testid="student-attempt">
      <td className="px-4 py-2.5 font-medium text-[var(--admin-text-secondary)]">
        Versuch {attempt.attempt_number ?? "?"}
        {isBest && <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-700">Bestes</span>}
      </td>
      <td className="px-4 py-2.5 font-bold tabular-nums text-[var(--admin-text-primary)]">{status}</td>
      <td className="px-4 py-2.5 text-[var(--admin-text-muted)]">{dateText(attempt.completed_at ?? attempt.started_at)}</td>
      <td className="px-4 py-2.5 text-right">
        {attempt.certificate_available ? (
          <AdminButton size="sm" variant="secondary" onClick={download} disabled={pending} data-testid="student-attempt-certificate">
            {pending ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
            Zertifikat
          </AdminButton>
        ) : (
          <span className="text-xs text-[var(--admin-text-muted)]">—</span>
        )}
        {failed && <p className="mt-1 text-xs text-[var(--admin-danger)]">Fehler beim Erstellen.</p>}
      </td>
    </tr>
  );
}
