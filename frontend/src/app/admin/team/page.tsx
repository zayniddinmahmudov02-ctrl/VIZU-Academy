"use client";

import { useEffect, useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GraduationCap, Search, ShieldCheck, ShieldOff, UserCheck, UserMinus, UserPlus, Users, UserRoundPlus } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import Avatar from "@/components/ui/avatar";
import { CreateTeacherDialog, formatDe, TeacherDetailDialog } from "@/features/admin/components/team/teacher-dialogs";
import { getTeamOverview, listTeamTeachers, setAdminTeaches, type TeamTeacher } from "@/features/admin/services/team-service";
import { changeUserRole, listUsers } from "@/features/admin/services/users-service";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { teamError } from "@/features/admin/components/team/teacher-dialogs";
import type { UserListItem } from "@/features/admin/types/user.types";

function displayName(item: UserListItem): string {
  return [item.first_name, item.last_name].filter(Boolean).join(" ") || item.username;
}

function Stat({ icon: Icon, label, value, testId }: { icon: typeof Users; label: string; value: number | string; testId: string }) {
  return (
    <AdminCard className="flex items-center gap-3 !p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]"><Icon size={18} /></div>
      <div>
        <p className="text-xl font-bold text-[var(--admin-text-primary)]" data-testid={testId}>{value}</p>
        <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
      </div>
    </AdminCard>
  );
}

/** Admin → Team: every teacher in one place — overview, list with search / filters, "Lehrer hinzufügen" (login + temporary
 * password + Kontroll Ja / Nein), and per teacher: profile, Kontroll permission (+ history), status, password reset, groups and
 * courses. Backend: /api/v1/admin/team/* (SUPER_ADMIN). Promoting an existing student stays possible at the bottom. */
export default function TeamPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [control, setControl] = useState("");
  const [page, setPage] = useState(1);
  const [creating, setCreating] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);
  const [studentSearch, setStudentSearch] = useState("");
  const [promoting, setPromoting] = useState<UserListItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = window.setTimeout(() => { setQ(search.trim()); setPage(1); }, 300);
    return () => window.clearTimeout(id);
  }, [search]);

  const overview = useQuery({ queryKey: ["admin-team", "overview"], queryFn: getTeamOverview });
  const teachers = useQuery({
    queryKey: ["admin-team", "list", q, status, control, page],
    queryFn: () => listTeamTeachers({ search: q || undefined, status: status || undefined, control: control || undefined, page, page_size: 25 }),
    placeholderData: keepPreviousData,
  });

  const trimmedSearch = studentSearch.trim();
  const { data: studentResults, isLoading: searchLoading } = useQuery({
    queryKey: ["admin-team-student-search", trimmedSearch],
    queryFn: () => listUsers({ role: "STUDENT", search: trimmedSearch, page_size: 20 }),
    enabled: trimmedSearch.length >= 2,
  });
  // the Super Admin's own account can teach as well (Team row + My Teacher); role and admin rights stay
  const { user: me } = useCurrentUser();
  const selfTeach = useMutation({
    mutationFn: () => setAdminTeaches(me!.id, true),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin-team"] }); setError(null); if (me) setOpenId(me.id); },
    onError: (err) => setError(teamError(err)),
  });

  const promoteMutation = useMutation({
    mutationFn: () => changeUserRole(promoting!.id, "TEACHER"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-team"] });
      queryClient.invalidateQueries({ queryKey: ["admin-team-student-search"] });
      setPromoting(null);
      setError(null);
    },
    onError: () => setError("Rolle konnte nicht geändert werden."),
  });

  const columns: DataTableColumn<TeamTeacher>[] = [
    { key: "id", header: "ID", render: (t) => <span className="font-mono text-xs" title={t.id}>{t.id.slice(0, 8)}</span> },
    { key: "name", header: "Name", render: (t) => (
      <span className="flex flex-wrap items-center gap-1.5">
        <button type="button" className="font-medium text-[var(--admin-text-primary)] hover:text-[var(--admin-primary)]" onClick={() => setOpenId(t.id)} data-testid="team-open">{t.name}</button>
        {t.admin_account && <span className="rounded-full bg-[var(--admin-primary)]/15 px-2 py-0.5 text-[11px] font-semibold text-[var(--admin-primary)]" data-testid="team-admin-badge">Admin + Lehrkraft</span>}
      </span>
    ) },
    { key: "username", header: "Benutzername", render: (t) => <span className="font-mono text-xs">{t.username}</span> },
    { key: "email", header: "E-Mail", render: (t) => t.email ?? <span className="text-[var(--admin-text-muted)]">—</span> },
    { key: "groups", header: "Gruppen", render: (t) => t.group_count },
    { key: "courses", header: "Kurse", render: (t) => t.course_count },
    { key: "status", header: "Status", render: (t) => (
      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${t.status === "active" ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]" : t.status === "blocked" ? "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]" : "bg-white/5 text-[var(--admin-text-muted)]"}`}>
        {t.status === "active" ? "Aktiv" : t.status === "blocked" ? "Gesperrt" : "Inaktiv"}
      </span>
    ) },
    { key: "control", header: "Kontroll", render: (t) => t.can_access_student_control
      ? <span className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--admin-accent)]" data-testid="team-control-yes"><ShieldCheck size={14} /> Ja</span>
      : <span className="inline-flex items-center gap-1 text-xs text-[var(--admin-text-muted)]" data-testid="team-control-no"><ShieldOff size={14} /> Nein</span> },
    { key: "created", header: "Angelegt", render: (t) => formatDe(t.created_at, false) },
    { key: "login", header: "Letzter Login", render: (t) => t.last_login_at ? formatDe(t.last_login_at) : <span className="text-[var(--admin-text-muted)]">noch nie</span> },
    { key: "open", header: "", className: "text-right", render: (t) => <AdminButton size="sm" variant="secondary" onClick={() => setOpenId(t.id)}>Verwalten</AdminButton> },
  ];

  const studentColumns: DataTableColumn<UserListItem>[] = [
    { key: "avatar", header: "", className: "w-12", render: (item) => <Avatar src={item.profile_image ?? undefined} name={displayName(item)} size={32} /> },
    { key: "name", header: "Name", render: (item) => displayName(item) },
    { key: "user", header: "Login", render: (item) => <div><p className="font-medium">{item.username}</p><p className="text-xs text-[var(--admin-text-muted)]">{item.email}</p></div> },
    { key: "action", header: "", className: "text-right", render: (item) => (
      <div className="flex justify-end"><AdminButton size="sm" variant="secondary" onClick={() => setPromoting(item)}><UserPlus size={14} /> Als Lehrer hinzufügen</AdminButton></div>
    ) },
  ];

  const o = overview.data;
  return (
    <div data-testid="admin-team">
      <AdminPageHeader title="Team" description="Alle Lehrkräfte zentral verwalten: Konten, Kontroll-Berechtigung, Gruppen und Kurse."
                       action={
                         <div className="flex flex-wrap gap-2">
                           {o && o.self_teaches === false && me && (
                             <AdminButton variant="secondary" onClick={() => selfTeach.mutate()} disabled={selfTeach.isPending} data-testid="team-self-teach"
                                          title="Ihr Admin-Konto wird zusätzlich als Lehrkraft geführt (Team + My Teacher). Rolle und Admin-Rechte bleiben.">
                               <GraduationCap size={16} /> Mein Konto als Lehrkraft
                             </AdminButton>
                           )}
                           <AdminButton onClick={() => setCreating(true)} data-testid="team-add"><UserRoundPlus size={16} /> Lehrer hinzufügen</AdminButton>
                         </div>
                       } />
      {error && !promoting && <p className="mb-4 rounded-lg bg-[var(--admin-danger)]/10 px-3 py-2 text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Stat icon={Users} label="Lehrkräfte gesamt" value={o?.total ?? "…"} testId="team-total" />
        <Stat icon={UserCheck} label="Aktiv" value={o?.active ?? "…"} testId="team-active" />
        <Stat icon={UserMinus} label="Inaktiv" value={o?.inactive ?? "…"} testId="team-inactive" />
        <Stat icon={ShieldCheck} label="Mit Kontroll-Zugriff" value={o?.with_control ?? "…"} testId="team-with-control" />
        <Stat icon={ShieldOff} label="Ohne Kontroll-Zugriff" value={o?.without_control ?? "…"} testId="team-without-control" />
        <Stat icon={UserRoundPlus} label={`Neu (${o?.new_days ?? 30} Tage)`} value={o?.new ?? "…"} testId="team-new" />
      </div>

      <AdminCard className="mb-6">
        <div className="mb-4 flex flex-wrap gap-2">
          <div className="relative min-w-[14rem] flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
            <AdminInput value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Name, Benutzername oder E-Mail..." className="pl-9" data-testid="team-search" />
          </div>
          <div className="w-44"><AdminSelect value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Status"><option value="">Status: alle</option><option value="active">Aktiv</option><option value="inactive">Inaktiv</option></AdminSelect></div>
          <div className="w-48"><AdminSelect value={control} onChange={(e) => { setControl(e.target.value); setPage(1); }} aria-label="Kontroll" data-testid="team-control-filter"><option value="">Kontroll: alle</option><option value="yes">Kontroll: Ja</option><option value="no">Kontroll: Nein</option></AdminSelect></div>
        </div>
        <DataTable columns={columns} data={teachers.data?.items} isLoading={teachers.isLoading} getRowId={(t) => t.id} emptyMessage="Noch keine Lehrkräfte." />
        {teachers.data && teachers.data.total > teachers.data.page_size && (
          <div className="mt-3 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
            <span>Seite {page} von {Math.ceil(teachers.data.total / teachers.data.page_size)} · {teachers.data.total} Lehrkräfte</span>
            <span className="flex gap-2">
              <AdminButton size="sm" variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Zurück</AdminButton>
              <AdminButton size="sm" variant="secondary" disabled={page * teachers.data.page_size >= teachers.data.total} onClick={() => setPage(page + 1)}>Weiter</AdminButton>
            </span>
          </div>
        )}
      </AdminCard>

      <AdminCard>
        <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">Bestehenden Studenten zum Lehrer ernennen</h2>
        <p className="mb-4 text-sm text-[var(--admin-text-secondary)]">Suche nach Nickname oder E-Mail, um einem vorhandenen Konto die Rolle Lehrer zu geben (Kontroll bleibt „Nein“).</p>
        <div className="relative mb-4 max-w-md">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
          <AdminInput value={studentSearch} onChange={(e) => setStudentSearch(e.target.value)} placeholder="Nickname oder E-Mail..." className="pl-9" />
        </div>
        {trimmedSearch.length >= 2 && (
          <DataTable columns={studentColumns} data={studentResults?.items} isLoading={searchLoading} getRowId={(item) => item.id} emptyMessage="Keine Studenten gefunden." />
        )}
      </AdminCard>

      <CreateTeacherDialog open={creating} onOpenChange={setCreating} />
      {openId && <TeacherDetailDialog teacherId={openId} onClose={() => setOpenId(null)} />}

      <FormDialog open={!!promoting} onOpenChange={(open) => !open && setPromoting(null)} title="Als Lehrer hinzufügen"
                  description={promoting ? `"${displayName(promoting)}" (${promoting.email}) erhält die Rolle Lehrer.` : undefined}
                  footer={<>
                    <AdminButton variant="ghost" onClick={() => setPromoting(null)} disabled={promoteMutation.isPending}>Abbrechen</AdminButton>
                    <AdminButton onClick={() => promoteMutation.mutate()} disabled={promoteMutation.isPending}>{promoteMutation.isPending ? "Wird gespeichert..." : "Bestätigen"}</AdminButton>
                  </>}>
        <p className="text-sm text-[var(--admin-text-secondary)]">Der Nutzer erhält Zugriff auf das Lehrer-Panel und kann im Profilmenü jederzeit zwischen Student- und Lehrer-Panel wechseln.</p>
        {error && <p className="mt-2 text-sm text-[var(--admin-danger)]">{error}</p>}
      </FormDialog>
    </div>
  );
}
