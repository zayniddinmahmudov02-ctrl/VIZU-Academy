"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import { listVizuMultilevelAttempts } from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type { VizuMultilevelAdminAttemptItem } from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";
import VizuMultilevelAttemptsTable from "./attempts-table";
import SprechenAttemptDetail from "./sprechen-attempt-detail";

const PAGE_SIZE = 20;
const LEVELS = ["A1", "A2", "B1", "B2", "C1"];

const SKILL_ROWS: { key: keyof VizuMultilevelAdminAttemptItem; label: string }[] = [
  { key: "lesen_level", label: "Lesen" },
  { key: "hoeren_level", label: "Hören" },
  { key: "schreiben_level", label: "Schreiben" },
  { key: "sprechen_level", label: "Sprechen" },
  { key: "overall_level", label: "Gesamt" },
];

function formatDateTime(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function VizuMultilevelResultsTab() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<VizuMultilevelAdminAttemptItem | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["vizu-multilevel-admin-attempts", page, search, level, status],
    queryFn: () =>
      listVizuMultilevelAttempts({
        page,
        page_size: PAGE_SIZE,
        search: search || undefined,
        level: level || undefined,
        status: status || undefined,
      }),
  });

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
          <AdminInput
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Suche nach Benutzername oder E-Mail..."
            className="pl-9"
          />
        </div>
        <AdminSelect
          value={level}
          onChange={(e) => {
            setLevel(e.target.value);
            setPage(1);
          }}
          className="w-40"
        >
          <option value="">Alle Niveaus</option>
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </AdminSelect>
        <AdminSelect
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          className="w-52"
        >
          <option value="">Alle Status</option>
          <option value="COMPLETED">Abgeschlossen</option>
          <option value="IN_PROGRESS">In Bearbeitung</option>
        </AdminSelect>
      </div>

      <VizuMultilevelAttemptsTable
        items={data?.items}
        isLoading={isLoading}
        onSelect={setSelected}
        emptyMessage="Keine Ergebnisse gefunden."
      />

      {data && data.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
          <span>
            Seite {data.page} von {data.total_pages} ({data.total} Tests)
          </span>
          <div className="flex gap-2">
            <AdminButton variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft size={14} />
            </AdminButton>
            <AdminButton
              variant="secondary"
              size="sm"
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              <ChevronRight size={14} />
            </AdminButton>
          </div>
        </div>
      )}

      <FormDialog
        open={!!selected}
        onOpenChange={(open) => !open && setSelected(null)}
        title={selected ? selected.student_name : ""}
        description={selected ? `${selected.username} · ${selected.email}` : undefined}
        size="lg"
      >
        {selected && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-[var(--admin-text-muted)]">Gestartet</p>
                <p className="font-semibold text-[var(--admin-text-primary)]">{formatDateTime(selected.started_at)}</p>
              </div>
              <div>
                <p className="text-[var(--admin-text-muted)]">Beendet</p>
                <p className="font-semibold text-[var(--admin-text-primary)]">{formatDateTime(selected.completed_at)}</p>
              </div>
              <div>
                <p className="text-[var(--admin-text-muted)]">Dauer</p>
                <p className="font-semibold text-[var(--admin-text-primary)]">
                  {selected.duration_minutes !== null ? `${selected.duration_minutes} Min.` : "—"}
                </p>
              </div>
              <div>
                <p className="text-[var(--admin-text-muted)]">Lesen-Punkte</p>
                <p className="font-semibold text-[var(--admin-text-primary)]">
                  {selected.lesen_score !== null ? `${selected.lesen_score}/100` : "—"}
                </p>
              </div>
            </div>

            <div className="overflow-hidden rounded-xl ring-1 ring-[var(--admin-border)]">
              <table className="w-full text-left text-sm">
                <tbody className="divide-y divide-[var(--admin-border)]">
                  {SKILL_ROWS.map((row) => (
                    <tr key={row.key}>
                      <td className="px-4 py-2.5 font-medium text-[var(--admin-text-secondary)]">{row.label}</td>
                      <td className="px-4 py-2.5 text-right font-bold text-[var(--admin-text-primary)]">
                        {(selected[row.key] as string | null) ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold text-[var(--admin-text-primary)]">Sprechen — Aufnahmen, Transkript & KI-Bewertung</p>
              <SprechenAttemptDetail attemptId={selected.id} />
            </div>
          </div>
        )}
      </FormDialog>
    </div>
  );
}
