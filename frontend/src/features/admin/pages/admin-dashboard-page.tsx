"use client";

import { useEffect, useState } from "react";
import {
  Award,
  BarChart3,
  BookOpen,
  CreditCard,
  Crown,
  FileText,
  GraduationCap,
  ShieldCheck,
  TrendingUp,
  UserPlus,
  Users,
  Wallet,
} from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useAdminDashboard } from "../hooks/use-admin-dashboard";
import StatCard from "../components/stat-card";
import RevenueChart from "../components/revenue-chart";
import UserGrowthChart from "../components/user-growth-chart";
import ListCard from "../components/list-card";
import AdminLoading from "../components/admin-loading";

function formatCurrency(value: number): string {
  return `${new Intl.NumberFormat("de-DE").format(value)} UZS`;
}

function formatDateTime(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function AdminDashboardPage() {
  const { user } = useCurrentUser();
  const { data, loading, error } = useAdminDashboard();

  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const dateLabel = now
    ? new Intl.DateTimeFormat("de-DE", { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(now)
    : "";
  const timeLabel = now
    ? new Intl.DateTimeFormat("de-DE", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(now)
    : "";

  if (loading) {
    return <AdminLoading />;
  }

  if (error || !data) {
    return (
      <div className="admin-glass rounded-2xl p-8 text-center">
        <p className="text-sm font-semibold text-white">Dashboard data unavailable</p>
        <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
          Could not reach the admin API. Check that the backend is running and reachable.
        </p>
      </div>
    );
  }

  const stats = data.stats;

  const statCards = [
    { label: "Total Users", value: String(stats.totalUsers), icon: Users, gradient: "from-[#5b5bf8] to-[#7c3aed]" },
    { label: "Premium Users", value: String(stats.premiumUsers), icon: Crown, gradient: "from-[#22c55e] to-emerald-400" },
    { label: "Trial Users", value: String(stats.trialUsers), icon: UserPlus, gradient: "from-[#f59e0b] to-amber-400" },
    { label: "Revenue Today", value: formatCurrency(stats.revenueToday), icon: Wallet, gradient: "from-[#5b5bf8] to-[#7c3aed]" },
    { label: "Revenue This Month", value: formatCurrency(stats.revenueMonth), icon: TrendingUp, gradient: "from-[#7c3aed] to-purple-400" },
    { label: "Revenue This Year", value: formatCurrency(stats.revenueYear), icon: BarChart3, gradient: "from-[#5b5bf8] to-blue-400" },
    { label: "Certificates", value: String(stats.certificates), icon: Award, gradient: "from-amber-500 to-[#f59e0b]" },
    { label: "Courses", value: String(stats.courses), icon: BookOpen, gradient: "from-blue-500 to-[#5b5bf8]" },
    { label: "Lessons", value: String(stats.lessons), icon: GraduationCap, gradient: "from-emerald-500 to-[#22c55e]" },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="admin-glass flex flex-wrap items-center justify-between gap-4 rounded-2xl p-6">
        <div>
          <h1 className="text-xl font-bold text-white">
            Welcome back, {user?.username ?? "Super Admin"} 👋
          </h1>
          <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">{dateLabel}</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-lg font-bold tabular-nums text-white">{timeLabel}</p>
            <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">Local time</p>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-[#22c55e]/30 bg-[#22c55e]/10 px-3 py-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-[#22c55e]" />
            <span className="text-xs font-semibold text-[#22c55e]">
              Server {data.serverStatus}
            </span>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">
        {statCards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <RevenueChart data={data.revenueChart} />
        <UserGrowthChart data={data.userGrowthChart} />
      </div>

      {/* Lists */}
      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <ListCard
          title="Most Popular Courses"
          isEmpty={data.popularCourses.length === 0}
          emptyLabel="No courses yet."
        >
          {data.popularCourses.map((course) => (
            <div
              key={course.id}
              className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]"
            >
              <div className="min-w-0">
                <p className="truncate font-medium text-white">{course.title}</p>
                <p className="text-xs text-[var(--admin-text-muted)]">{course.level}</p>
              </div>
              <span className="shrink-0 rounded-full bg-white/5 px-2.5 py-1 text-xs font-semibold text-[var(--admin-text-secondary)]">
                {course.enrollments}
              </span>
            </div>
          ))}
        </ListCard>

        <ListCard
          title="Most Active Users"
          isEmpty={data.activeUsers.length === 0}
          emptyLabel="No login activity yet."
        >
          {data.activeUsers.map((u) => (
            <div key={u.id} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div className="min-w-0">
                <p className="truncate font-medium text-white">{u.username}</p>
                <p className="truncate text-xs text-[var(--admin-text-muted)]">{u.email}</p>
              </div>
              <span className="shrink-0 text-xs text-[var(--admin-text-muted)]">
                {formatDateTime(u.lastLogin)}
              </span>
            </div>
          ))}
        </ListCard>

        <ListCard
          title="Latest Registrations"
          isEmpty={data.recentRegistrations.length === 0}
          emptyLabel="No registrations yet."
        >
          {data.recentRegistrations.map((r) => (
            <div key={r.id} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div className="min-w-0">
                <p className="truncate font-medium text-white">{r.username}</p>
                <p className="truncate text-xs text-[var(--admin-text-muted)]">{r.email}</p>
              </div>
              <span className="shrink-0 text-xs text-[var(--admin-text-muted)]">
                {formatDateTime(r.createdAt)}
              </span>
            </div>
          ))}
        </ListCard>

        <ListCard
          title="Latest Payments"
          isEmpty={data.recentPayments.length === 0}
          emptyLabel="No payments yet."
        >
          {data.recentPayments.map((p) => (
            <div key={p.id} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div className="flex min-w-0 items-center gap-2.5">
                <CreditCard size={14} className="shrink-0 text-[var(--admin-text-muted)]" />
                <div className="min-w-0">
                  <p className="truncate font-medium text-white">{p.userEmail}</p>
                  <p className="truncate text-xs text-[var(--admin-text-muted)]">{p.courseTitle}</p>
                </div>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-xs font-semibold text-white">
                  {p.amount} {p.currency}
                </p>
                <p className="text-[10px] uppercase text-[var(--admin-text-muted)]">{p.status}</p>
              </div>
            </div>
          ))}
        </ListCard>

        <ListCard
          title="Recent Certificates"
          isEmpty={data.recentCertificates.length === 0}
          emptyLabel="No certificates yet."
        >
          {data.recentCertificates.map((c) => (
            <div key={c.id} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div className="flex min-w-0 items-center gap-2.5">
                <ShieldCheck size={14} className="shrink-0 text-[var(--admin-text-muted)]" />
                <div className="min-w-0">
                  <p className="truncate font-medium text-white">{c.userEmail}</p>
                  <p className="truncate text-xs text-[var(--admin-text-muted)]">{c.courseTitle}</p>
                </div>
              </div>
              <span className="shrink-0 rounded-full bg-white/5 px-2.5 py-1 text-xs font-semibold text-[var(--admin-text-secondary)]">
                {c.level}
              </span>
            </div>
          ))}
        </ListCard>

        <ListCard
          title="Latest Activities"
          isEmpty={data.recentActivities.length === 0}
          emptyLabel="No activity yet."
        >
          {data.recentActivities.map((a, i) => (
            <div key={i} className="flex items-center gap-2.5 rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <FileText size={14} className="shrink-0 text-[var(--admin-text-muted)]" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-white">{a.title}</p>
              </div>
              <span className="shrink-0 text-[10px] text-[var(--admin-text-muted)]">
                {formatDateTime(a.timestamp)}
              </span>
            </div>
          ))}
        </ListCard>
      </div>
    </div>
  );
}
