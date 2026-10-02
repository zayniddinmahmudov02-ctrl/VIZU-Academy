"use client";

import type { LucideIcon } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";

export const SKILL_LABELS: Record<string, string> = {
  LESEN: "Lesen",
  HOEREN: "Hören",
  SCHREIBEN: "Schreiben",
  SPRECHEN: "Sprechen",
};

export function StatCard({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <AdminCard className="flex items-center gap-3.5 transition-transform duration-200 hover:-translate-y-0.5">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
        <Icon size={19} />
      </div>
      <div className="min-w-0">
        <p className="truncate text-[11px] font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">
          {label}
        </p>
        <p className="mt-0.5 truncate text-lg font-bold text-[var(--admin-text-primary)]">{value}</p>
      </div>
    </AdminCard>
  );
}

export function StatsSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <AdminCard key={i} className="h-[84px] animate-pulse">
          <div className="h-3 w-20 rounded bg-white/5" />
          <div className="mt-3 h-6 w-16 rounded bg-white/5" />
        </AdminCard>
      ))}
    </div>
  );
}

export function ProgressBar({
  label,
  percent,
  right,
}: {
  label: string;
  percent: number;
  right?: string;
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-sm">
        <span className="font-semibold text-[var(--admin-text-primary)]">{label}</span>
        <span className="text-[var(--admin-text-muted)]">{right}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--admin-border)]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[var(--admin-primary)] to-[var(--admin-primary-hover)] transition-all"
          style={{ width: `${Math.max(percent, percent > 0 ? 2 : 0)}%` }}
        />
      </div>
    </div>
  );
}
