"use client";

import {
  Award,
  BookOpenCheck,
  Cpu,
  Database,
  HardDrive,
  MemoryStick,
  Radio,
  Server,
  Shield,
  Timer,
  UserPlus,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import type { DashboardActivityItem, ServerHealth as ServerHealthType } from "@/features/admin/types/enterprise-dashboard.types";

const ACTIVITY_ICONS: Record<string, LucideIcon> = {
  registration: UserPlus,
  premium_purchase: Wallet,
  lesson_completed: BookOpenCheck,
  mock_test_created: Award,
  admin_action: Shield,
  certificate_issued: Award,
};

function timeAgo(timestamp: string): string {
  const diffMs = Date.now() - new Date(timestamp).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function ActivityHealthSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {[0, 1].map((i) => (
        <AdminCard key={i} className="h-[320px] animate-pulse">
          <div className="h-3 w-32 rounded bg-white/5" />
          <div className="mt-6 space-y-2">
            {[0, 1, 2, 3].map((j) => (
              <div key={j} className="h-10 rounded-lg bg-white/5" />
            ))}
          </div>
        </AdminCard>
      ))}
    </div>
  );
}

function RecentActivity({ items }: { items: DashboardActivityItem[] }) {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Recent Activity</h3>
      {items.length === 0 ? (
        <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Noch keine Aktivitäten.</p>
      ) : (
        <div className="max-h-[380px] space-y-1.5 overflow-y-auto">
          {items.map((item, index) => {
            const Icon = ACTIVITY_ICONS[item.type] ?? Radio;
            return (
              <div key={`${item.type}-${index}`} className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-white/[0.02]">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/5 text-[var(--admin-text-secondary)]">
                  <Icon size={14} />
                </div>
                <p className="min-w-0 flex-1 truncate text-sm text-[var(--admin-text-primary)]">{item.title}</p>
                <span className="shrink-0 text-xs text-[var(--admin-text-muted)]">{timeAgo(item.timestamp)}</span>
              </div>
            );
          })}
        </div>
      )}
    </AdminCard>
  );
}

function HealthRow({
  icon: Icon,
  label,
  ok,
  detail,
}: {
  icon: LucideIcon;
  label: string;
  ok: boolean | null;
  detail: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-white/[0.02] p-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/5 text-[var(--admin-text-secondary)]">
        <Icon size={16} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-[var(--admin-text-primary)]">{label}</p>
        <p className="truncate text-xs text-[var(--admin-text-muted)]">{detail}</p>
      </div>
      {ok !== null && (
        <span
          className={`h-2.5 w-2.5 shrink-0 rounded-full ${
            ok ? "bg-[var(--admin-accent)]" : "bg-[var(--admin-danger)]"
          }`}
        />
      )}
    </div>
  );
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function ServerHealth({ health }: { health: ServerHealthType }) {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Server Health</h3>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <HealthRow icon={Server} label="Backend" ok={health.backend} detail={health.backend ? "Operational" : "Down"} />
        <HealthRow
          icon={Database}
          label="Postgres"
          ok={health.postgres}
          detail={health.postgres ? `${health.postgres_latency_ms}ms latency` : "Unreachable"}
        />
        <HealthRow
          icon={HardDrive}
          label="Storage"
          ok={health.storage_used_percent !== null ? health.storage_used_percent < 90 : null}
          detail={health.storage_used_percent !== null ? `${health.storage_used_percent}% used` : "Unavailable"}
        />
        <HealthRow
          icon={HardDrive}
          label="Disk"
          ok={health.disk_used_percent !== null ? health.disk_used_percent < 90 : null}
          detail={health.disk_used_percent !== null ? `${health.disk_used_percent}% used` : "Unavailable"}
        />
        <HealthRow
          icon={Cpu}
          label="CPU"
          ok={health.cpu_percent !== null ? health.cpu_percent < 90 : null}
          detail={health.cpu_percent !== null ? `${health.cpu_percent}%` : "Unavailable on this host"}
        />
        <HealthRow
          icon={MemoryStick}
          label="RAM"
          ok={health.ram_percent !== null ? health.ram_percent < 90 : null}
          detail={health.ram_percent !== null ? `${health.ram_percent}%` : "Unavailable on this host"}
        />
        <HealthRow icon={Timer} label="Uptime" ok={null} detail={formatUptime(health.uptime_seconds)} />
      </div>
    </AdminCard>
  );
}

export default function DashboardActivityHealth({
  activity,
  health,
}: {
  activity: DashboardActivityItem[];
  health: ServerHealthType;
}) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <RecentActivity items={activity} />
      <ServerHealth health={health} />
    </div>
  );
}
