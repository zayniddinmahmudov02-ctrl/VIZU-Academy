"use client";

import {
  Award,
  BookOpen,
  Calendar,
  ClipboardCheck,
  Crown,
  UserCheck,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import type { DashboardKPIs } from "@/features/admin/types/enterprise-dashboard.types";

function formatCurrency(value: number): string {
  return `${value.toLocaleString("de-DE")} UZS`;
}

interface KpiDef {
  key: keyof DashboardKPIs;
  label: string;
  icon: LucideIcon;
  format?: (value: number) => string;
}

const KPI_DEFS: KpiDef[] = [
  { key: "total_users", label: "Total Users", icon: Users },
  { key: "active_users_30d", label: "Active Users (30d)", icon: UserCheck },
  { key: "premium_members", label: "Premium Members", icon: Crown },
  { key: "total_revenue", label: "Total Revenue", icon: Wallet, format: formatCurrency },
  { key: "active_courses", label: "Active Courses", icon: BookOpen },
  { key: "total_model_tests", label: "Model Tests", icon: ClipboardCheck },
  { key: "certificates_issued", label: "Certificates Issued", icon: Award },
  { key: "todays_registrations", label: "Today's Registrations", icon: Calendar },
];

export function KpiCardsSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {KPI_DEFS.map((def) => (
        <AdminCard key={def.key} className="h-[84px] animate-pulse">
          <div className="h-3 w-20 rounded bg-white/5" />
          <div className="mt-3 h-6 w-16 rounded bg-white/5" />
        </AdminCard>
      ))}
    </div>
  );
}

export default function DashboardKpiCards({ kpis }: { kpis: DashboardKPIs }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {KPI_DEFS.map((def) => {
        const Icon = def.icon;
        const raw = kpis[def.key];
        const value = def.format ? def.format(raw) : raw.toLocaleString("de-DE");
        return (
          <AdminCard
            key={def.key}
            className="flex items-center gap-3.5 transition-transform duration-200 hover:-translate-y-0.5"
          >
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
              <Icon size={19} />
            </div>
            <div className="min-w-0">
              <p className="truncate text-[11px] font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">
                {def.label}
              </p>
              <p className="mt-0.5 truncate text-lg font-bold text-[var(--admin-text-primary)]">{value}</p>
            </div>
          </AdminCard>
        );
      })}
    </div>
  );
}
