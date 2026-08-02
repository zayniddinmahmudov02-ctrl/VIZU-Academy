"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Award,
  BookOpen,
  Crown,
  GraduationCap,
  Users,
  Wallet,
} from "lucide-react";

import { AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import MiniBarChart from "@/components/admin/mini-bar-chart";
import { getAdminDashboardOverview } from "@/features/admin/services/dashboard-service";

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Users;
  label: string;
  value: string | number;
}) {
  return (
    <AdminCard className="flex items-center gap-4">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
        <Icon size={19} />
      </div>
      <div className="min-w-0">
        <p className="truncate text-xs font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">
          {label}
        </p>
        <p className="mt-0.5 text-xl font-bold text-[var(--admin-text-primary)]">{value}</p>
      </div>
    </AdminCard>
  );
}

export default function AdminDashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-dashboard-overview"],
    queryFn: getAdminDashboardOverview,
  });

  return (
    <div>
      <AdminPageHeader
        title="Dashboard"
        description="Überblick über Plattform-Aktivität, Umsatz und Inhalte."
      />

      {isLoading && (
        <div className="flex justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-white/10 border-t-[var(--admin-primary)]" />
        </div>
      )}

      {isError && (
        <AdminCard>
          <p className="text-sm text-[var(--admin-danger)]">
            Dashboard-Daten konnten nicht geladen werden.
          </p>
        </AdminCard>
      )}

      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
            <StatCard icon={Users} label="Nutzer gesamt" value={data.stats.total_users} />
            <StatCard icon={Crown} label="Premium" value={data.stats.premium_users} />
            <StatCard icon={GraduationCap} label="Testphase" value={data.stats.trial_users} />
            <StatCard icon={BookOpen} label="Kurse" value={data.stats.courses} />
            <StatCard icon={Award} label="Zertifikate" value={data.stats.certificates} />
            <StatCard
              icon={Wallet}
              label="Umsatz (Monat)"
              value={data.stats.revenue_month.toLocaleString()}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <AdminCard>
              <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">
                Umsatzverlauf
              </h3>
              {data.revenue_chart.length > 0 ? (
                <MiniBarChart data={data.revenue_chart} />
              ) : (
                <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">
                  Noch keine Daten.
                </p>
              )}
            </AdminCard>

            <AdminCard>
              <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">
                Nutzerwachstum
              </h3>
              {data.user_growth_chart.length > 0 ? (
                <MiniBarChart data={data.user_growth_chart} />
              ) : (
                <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">
                  Noch keine Daten.
                </p>
              )}
            </AdminCard>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <AdminCard>
              <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">
                Beliebte Kurse
              </h3>
              <div className="space-y-3">
                {data.popular_courses.length === 0 && (
                  <p className="text-sm text-[var(--admin-text-muted)]">Keine Daten.</p>
                )}
                {data.popular_courses.map((course) => (
                  <div key={course.id} className="flex items-center justify-between text-sm">
                    <span className="truncate text-[var(--admin-text-primary)]">
                      {course.title} <span className="text-[var(--admin-text-muted)]">({course.level})</span>
                    </span>
                    <span className="shrink-0 font-semibold text-[var(--admin-primary)]">
                      {course.enrollments}
                    </span>
                  </div>
                ))}
              </div>
            </AdminCard>

            <AdminCard>
              <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">
                Neue Registrierungen
              </h3>
              <div className="space-y-3">
                {data.recent_registrations.length === 0 && (
                  <p className="text-sm text-[var(--admin-text-muted)]">Keine Daten.</p>
                )}
                {data.recent_registrations.map((reg) => (
                  <div key={reg.id} className="text-sm">
                    <p className="truncate text-[var(--admin-text-primary)]">{reg.username}</p>
                    <p className="truncate text-xs text-[var(--admin-text-muted)]">{reg.email}</p>
                  </div>
                ))}
              </div>
            </AdminCard>

            <AdminCard>
              <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">
                Letzte Aktivitäten
              </h3>
              <div className="space-y-3">
                {data.recent_activities.length === 0 && (
                  <p className="text-sm text-[var(--admin-text-muted)]">Keine Daten.</p>
                )}
                {data.recent_activities.map((activity, i) => (
                  <div key={i} className="text-sm">
                    <p className="truncate text-[var(--admin-text-primary)]">{activity.title}</p>
                    <p className="text-xs text-[var(--admin-text-muted)]">
                      {new Date(activity.timestamp).toLocaleString("de-DE")}
                    </p>
                  </div>
                ))}
              </div>
            </AdminCard>
          </div>
        </div>
      )}
    </div>
  );
}
