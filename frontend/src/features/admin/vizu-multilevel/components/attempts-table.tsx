"use client";

import Link from "next/link";
import { DataTableColumn } from "@/components/admin/data-table";
import DataTable from "@/components/admin/data-table";
import type { VizuMultilevelAdminAttemptItem } from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";

export const LEVEL_BADGE_CLASS =
  "rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-primary)]";

function formatDateTime(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function LevelCell({ level }: { level: string | null }) {
  return level ? <span className={LEVEL_BADGE_CLASS}>{level}</span> : <span className="text-[var(--admin-text-muted)]">—</span>;
}

function StatusBadge({ status }: { status: string }) {
  const completed = status === "COMPLETED";
  return (
    <span
      className={
        completed
          ? "rounded-full bg-[var(--admin-success,#22c55e)]/15 px-2 py-0.5 text-xs font-semibold text-[var(--admin-success,#22c55e)]"
          : "rounded-full bg-[var(--admin-warning,#f59e0b)]/15 px-2 py-0.5 text-xs font-semibold text-[var(--admin-warning,#f59e0b)]"
      }
    >
      {completed ? "Abgeschlossen" : "In Bearbeitung"}
    </span>
  );
}

interface Props {
  items: VizuMultilevelAdminAttemptItem[] | undefined;
  isLoading?: boolean;
  onSelect?: (item: VizuMultilevelAdminAttemptItem) => void;
  emptyMessage?: string;
}

export default function VizuMultilevelAttemptsTable({ items, isLoading, onSelect, emptyMessage }: Props) {
  const columns: DataTableColumn<VizuMultilevelAdminAttemptItem>[] = [
    {
      key: "student",
      header: "Student",
      render: (item) => (
        <Link
          href="/admin/users"
          className="font-semibold text-[var(--admin-text-primary)] hover:text-[var(--admin-primary)] hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {item.student_name}
        </Link>
      ),
    },
    { key: "username", header: "Benutzername", render: (item) => item.username },
    { key: "email", header: "E-Mail", render: (item) => item.email },
    { key: "started_at", header: "Gestartet", render: (item) => formatDateTime(item.started_at) },
    { key: "completed_at", header: "Beendet", render: (item) => formatDateTime(item.completed_at) },
    { key: "lesen", header: "Lesen", render: (item) => <LevelCell level={item.lesen_level} /> },
    { key: "hoeren", header: "Hören", render: (item) => <LevelCell level={item.hoeren_level} /> },
    { key: "schreiben", header: "Schreiben", render: (item) => <LevelCell level={item.schreiben_level} /> },
    { key: "sprechen", header: "Sprechen", render: (item) => <LevelCell level={item.sprechen_level} /> },
    { key: "overall", header: "Gesamt", render: (item) => <LevelCell level={item.overall_level} /> },
    { key: "status", header: "Status", render: (item) => <StatusBadge status={item.status} /> },
  ];

  return (
    <DataTable
      columns={columns}
      data={items}
      isLoading={isLoading}
      getRowId={(item) => item.id}
      onEdit={onSelect}
      emptyMessage={emptyMessage ?? "Keine Tests gefunden."}
    />
  );
}
