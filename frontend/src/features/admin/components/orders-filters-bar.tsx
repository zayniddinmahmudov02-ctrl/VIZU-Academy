"use client";

import { Search } from "lucide-react";

const STATUS_OPTIONS = ["PENDING", "APPROVED", "REJECTED", "EXPIRED", "REFUNDED"];
const PLAN_OPTIONS = ["MONTH_1", "MONTH_3", "MONTH_6", "MONTH_12"];

interface Props {
  search: string;
  onSearchChange: (value: string) => void;
  status: string | undefined;
  onStatusChange: (value: string | undefined) => void;
  plan: string | undefined;
  onPlanChange: (value: string | undefined) => void;
}

export default function OrdersFiltersBar({ search, onSearchChange, status, onStatusChange, plan, onPlanChange }: Props) {
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
        value={status ?? ""}
        onChange={(e) => onStatusChange(e.target.value || undefined)}
        className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] px-3 py-2.5 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
      >
        <option value="" className="bg-[#111827]">All statuses</option>
        {STATUS_OPTIONS.map((s) => (
          <option key={s} value={s} className="bg-[#111827]">{s}</option>
        ))}
      </select>

      <select
        value={plan ?? ""}
        onChange={(e) => onPlanChange(e.target.value || undefined)}
        className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] px-3 py-2.5 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
      >
        <option value="" className="bg-[#111827]">All plans</option>
        {PLAN_OPTIONS.map((p) => (
          <option key={p} value={p} className="bg-[#111827]">{p.replace("_", " ")}</option>
        ))}
      </select>
    </div>
  );
}
