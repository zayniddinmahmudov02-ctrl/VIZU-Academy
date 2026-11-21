"use client";

import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { CalendarDays, CalendarPlus, GraduationCap, Loader2, ShieldCheck, UserCheck, UserMinus, Users, UsersRound } from "lucide-react";

import { AdminButton, AdminCard, AdminInput } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { getStudentList, getStudentStats, type StudentListStatus } from "@/features/admin/services/student-stats-service";
import { cn } from "@/lib/utils";
import { formatCount, percentOf } from "./student-stats-format";

const fmtDate = (iso: string | null) => (iso ? new Date(iso).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" }) : "—");
const VIA: Record<string, string> = { email: "E-Mail", phone: "Telefon", telegram: "Telegram" };
const TABS: { id: StudentListStatus; label: string }[] = [
  { id: "all", label: "Alle" }, { id: "active", label: "Aktiv" }, { id: "inactive", label: "Inaktiv" }, { id: "blocked", label: "Gesperrt" },
  { id: "test_takers", label: "Test abgelegt" }, { id: "test_accounts", label: "Testkonten" },
];

function Stat({ label, value, hint, icon: Icon, testId }: { label: string; value: number; hint?: string; icon: typeof Users; testId: string }) {
  return (
    <AdminCard className="flex items-center gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]"><Icon size={18} /></div>
      <div className="min-w-0">
        <p className="line-clamp-2 text-[11px] font-medium uppercase leading-tight tracking-wide text-[var(--admin-text-muted)]">{label}</p>
        <p data-testid={testId} className="text-xl font-bold tabular-nums text-[var(--admin-text-primary)]">{formatCount(value)}</p>
        {hint && <p className="truncate text-[11px] text-[var(--admin-text-muted)]">{hint}</p>}
      </div>
    </AdminCard>
  );
}

function StudentList() {
  const [status, setStatus] = useState<StudentListStatus>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const q = useQuery({
    queryKey: ["admin-student-list", status, search, page],
    queryFn: () => getStudentList({ page, page_size: 20, status, search: search.trim() }),
    placeholderData: keepPreviousData,
    refetchInterval: 60_000,
  });
  const pages = q.data ? Math.max(1, Math.ceil(q.data.total / q.data.page_size)) : 1;

  return (
    <div data-testid="student-list">
    <AdminCard>
      <div className="mb-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div role="tablist" className="flex flex-wrap gap-1">
          {TABS.map((t) => (
            <button key={t.id} type="button" role="tab" aria-selected={status === t.id} data-testid={`student-list-tab-${t.id}`}
                    onClick={() => { setStatus(t.id); setPage(1); }}
                    className={cn("rounded-lg px-3 py-1.5 text-xs font-semibold", status === t.id ? "bg-[var(--admin-primary)] text-white" : "text-[var(--admin-text-secondary)] hover:bg-[var(--admin-hover)]")}>
              {t.label}
            </button>
          ))}
        </div>
        <AdminInput value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Name, E-Mail oder Telefon"
                    aria-label="Schüler suchen" data-testid="student-list-search" className="lg:w-72" />
      </div>
      {q.isError ? <p role="alert" className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(q.error, "Liste konnte nicht geladen werden.")}</p> : (
        <>
          <p className="mb-2 text-xs text-[var(--admin-text-muted)]"><span data-testid="student-list-total">{formatCount(q.data?.total ?? 0)}</span> Treffer</p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-xs text-[var(--admin-text-muted)]">
                <tr><th className="py-2 pr-3">Name</th><th className="py-2 pr-3">Kontakt</th><th className="py-2 pr-3">Über</th><th className="py-2 pr-3">Registriert</th>
                  <th className="py-2 pr-3">Letzter Login</th><th className="py-2 pr-3">Status</th><th className="py-2">Gruppen</th></tr>
              </thead>
              <tbody className="divide-y divide-[var(--admin-border)]">
                {q.data?.items.map((s) => (
                  <tr key={s.id} data-testid="student-row">
                    <td className="py-2 pr-3 font-medium text-[var(--admin-text-primary)]">{s.name}</td>
                    <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">{s.contact ?? "—"}</td>
                    <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">{VIA[s.registered_via]}</td>
                    <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">{fmtDate(s.created_at)}</td>
                    <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">{fmtDate(s.last_login)}</td>
                    <td className="py-2 pr-3 text-xs">
                      {s.is_blocked ? <span className="text-[var(--admin-danger)]">Gesperrt</span>
                        : s.is_active_student ? <span className="text-[var(--admin-success,#16a34a)]">Aktiv</span> : <span className="text-[var(--admin-text-muted)]">Inaktiv</span>}
                      {s.took_a_test && <span className="ml-2 text-[var(--admin-text-muted)]">· Test</span>}
                    </td>
                    <td className="py-2 tabular-nums text-[var(--admin-text-secondary)]">{s.groups}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {q.isFetching && <Loader2 size={14} className="mt-2 animate-spin text-[var(--admin-text-muted)]" />}
          <div className="mt-3 flex items-center justify-end gap-2 text-xs text-[var(--admin-text-muted)]">
            <AdminButton size="sm" variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Zurück</AdminButton>
            <span data-testid="student-list-page">Seite {page} / {pages}</span>
            <AdminButton size="sm" variant="secondary" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>Weiter</AdminButton>
          </div>
        </>
      )}
    </AdminCard>
    </div>
  );
}

/** Admin dashboard: students counted ONCE from the database (no cached or estimated number); refreshes every minute and on focus. */
export default function DashboardStudentStats() {
  const q = useQuery({ queryKey: ["admin-student-stats"], queryFn: getStudentStats, staleTime: 0, refetchInterval: 60_000, refetchOnWindowFocus: true });
  const [showList, setShowList] = useState(false);

  if (q.isLoading) return <AdminCard className="mb-6 h-[180px] animate-pulse"><span className="sr-only">Lädt…</span></AdminCard>;
  if (q.isError || !q.data) {
    return <AdminCard className="mb-6"><p role="alert" className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(q.error, "Schülerstatistik konnte nicht geladen werden.")}</p></AdminCard>;
  }
  const s = q.data;
  return (
    <section data-testid="student-stats" className="mb-6 space-y-4">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <AdminCard className="flex flex-col justify-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">Registrierte Schüler gesamt</p>
          <p data-testid="stat-total-students" className="mt-1 text-5xl font-extrabold tabular-nums text-[var(--admin-text-primary)]">{formatCount(s.total_students)}</p>
          <p className="mt-2 text-xs text-[var(--admin-text-muted)]">
            Jeder Schüler einmal, egal ob aktiv, abgemeldet oder gesperrt.
            {s.test_accounts > 0 && <> Ohne <span data-testid="stat-test-accounts">{formatCount(s.test_accounts)}</span> Testkonten (z. B. example.com).</>}
          </p>
          <p className="mt-1 text-[11px] text-[var(--admin-text-muted)]">Stand {fmtDate(s.computed_at)} · aktualisiert sich jede Minute</p>
        </AdminCard>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
          <Stat label={`Aktiv (${s.active_days} Tage)`} value={s.active_students} hint={percentOf(s.active_students, s.total_students)} icon={UserCheck} testId="stat-active-students" />
          <Stat label="Inaktiv" value={s.inactive_students} hint={s.blocked_students ? `davon ${formatCount(s.blocked_students)} gesperrt` : undefined} icon={UserMinus} testId="stat-inactive-students" />
          <Stat label="Lehrkräfte" value={s.total_teachers} icon={GraduationCap} testId="stat-teachers" />
          <Stat label="Admins" value={s.total_admins} hint={s.total_other_staff ? `+ ${formatCount(s.total_other_staff)} weiteres Personal` : undefined} icon={ShieldCheck} testId="stat-admins" />
          <Stat label="Gruppen" value={s.total_groups} hint={`${formatCount(s.active_groups)} aktiv`} icon={UsersRound} testId="stat-groups" />
          <Stat label="Neu heute" value={s.total_registrations_today} hint="Tag in Taschkent" icon={CalendarPlus} testId="stat-new-today" />
          <Stat label="Neu diesen Monat" value={s.total_registrations_this_month} icon={CalendarDays} testId="stat-new-month" />
          <Stat label="Konten gesamt" value={s.total_accounts} hint="alle Rollen + Testkonten" icon={Users} testId="stat-accounts" />
        </div>
      </div>
      <p className="text-xs text-[var(--admin-text-muted)]">
        Getrennt gezählt (nicht im Gesamtwert gemischt): Test abgelegt <b data-testid="stat-test-takers">{formatCount(s.test_takers)}</b> ·
        Unterricht begonnen <b data-testid="stat-participants">{formatCount(s.lesson_participants)}</b> · in Gruppen <b data-testid="stat-in-groups">{formatCount(s.students_in_groups)}</b> ·
        gesperrt <b>{formatCount(s.blocked_students)}</b>
      </p>
      {s.can_list_students && (
        <div>
          <AdminButton size="sm" variant="secondary" onClick={() => setShowList((v) => !v)} data-testid="student-list-toggle">
            {showList ? "Schülerliste ausblenden" : "Schülerliste anzeigen"}
          </AdminButton>
          {showList && <div className="mt-3"><StudentList /></div>}
        </div>
      )}
    </section>
  );
}
