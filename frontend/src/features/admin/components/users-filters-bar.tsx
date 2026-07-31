"use client";

import { Download, FileSpreadsheet, Search } from "lucide-react";

const ROLE_OPTIONS = [
  "SUPER_ADMIN",
  "ADMIN",
  "CONTENT_MANAGER",
  "PAYMENT_MANAGER",
  "SUPPORT",
  "TEACHER",
  "STUDENT",
];

const STATUS_OPTIONS = [
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "banned", label: "Banned" },
  { value: "suspended", label: "Suspended" },
  { value: "premium", label: "Premium" },
  { value: "trial", label: "Trial" },
];

interface Props {
  search: string;
  onSearchChange: (value: string) => void;
  role: string | undefined;
  onRoleChange: (value: string | undefined) => void;
  status: string | undefined;
  onStatusChange: (value: string | undefined) => void;
  onExportCsv: () => void;
  onExportXlsx: () => void;
  exporting: boolean;
  /** Restricts the role dropdown's choices — e.g. the "Admins" panel only
   *  offers staff roles, since it never shows students in the first place. */
  roleOptions?: string[];
}

export default function UsersFiltersBar({
  search,
  onSearchChange,
  role,
  onRoleChange,
  status,
  onStatusChange,
  onExportCsv,
  onExportXlsx,
  exporting,
  roleOptions = ROLE_OPTIONS,
}: Props) {
  return (
    <div className="admin-glass flex flex-wrap items-center gap-3 rounded-2xl p-4">
      <div className="relative min-w-[220px] flex-1">
        <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
        <input
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search by email or username…"
          className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] py-2.5 pl-9 pr-3 text-sm text-white placeholder:text-[var(--admin-text-muted)] outline-none focus:border-[var(--admin-primary)]/50"
        />
      </div>

      <select
        value={role ?? ""}
        onChange={(e) => onRoleChange(e.target.value || undefined)}
        className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] px-3 py-2.5 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
      >
        <option value="" className="bg-[#111827]">All roles</option>
        {roleOptions.map((r) => (
          <option key={r} value={r} className="bg-[#111827]">
            {r.replace(/_/g, " ")}
          </option>
        ))}
      </select>

      <select
        value={status ?? ""}
        onChange={(e) => onStatusChange(e.target.value || undefined)}
        className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] px-3 py-2.5 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
      >
        <option value="" className="bg-[#111827]">All statuses</option>
        {STATUS_OPTIONS.map((s) => (
          <option key={s.value} value={s.value} className="bg-[#111827]">
            {s.label}
          </option>
        ))}
      </select>

      <div className="ml-auto flex items-center gap-2">
        <button
          type="button"
          onClick={onExportCsv}
          disabled={exporting}
          className="flex items-center gap-2 rounded-xl border border-[var(--admin-border)] px-3 py-2.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white disabled:opacity-50"
        >
          <Download size={14} /> CSV
        </button>
        <button
          type="button"
          onClick={onExportXlsx}
          disabled={exporting}
          className="flex items-center gap-2 rounded-xl border border-[var(--admin-border)] px-3 py-2.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white disabled:opacity-50"
        >
          <FileSpreadsheet size={14} /> Excel
        </button>
      </div>
    </div>
  );
}
