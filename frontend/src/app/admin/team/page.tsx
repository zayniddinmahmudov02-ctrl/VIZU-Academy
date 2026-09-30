"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, UserPlus } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminPageHeader } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import Avatar from "@/components/ui/avatar";
import type { UserListItem } from "@/features/admin/types/user.types";
import { changeUserRole, listUsers } from "@/features/admin/services/users-service";

function displayName(item: UserListItem): string {
  return [item.first_name, item.last_name].filter(Boolean).join(" ") || item.username;
}

/** Reuses the existing admin Users API end to end — GET /admin/users
 * (role/search filters already supported) and PATCH /admin/users/{id}/role
 * (already validates against UserRole.ALL_ROLES). No new backend
 * endpoint, no parallel role system: "making someone a teacher" is
 * exactly the same role change the Users page's own role dropdown
 * already performs, just presented as a dedicated, task-focused flow
 * (search a student -> confirm -> done) instead of a generic edit form.
 * Panel access itself (who can reach /teacher, and the Settings/header
 * "Panel wechseln" switcher offering Student+Lehrer once role=TEACHER)
 * is already fully handled by the existing panel-switcher architecture
 * (usePanelSwitcher, AuthGuard, TeacherGuard, require_teacher_panel_access)
 * — nothing here duplicates or re-implements it. */
export default function TeamPage() {
  const queryClient = useQueryClient();
  const [studentSearch, setStudentSearch] = useState("");
  const [promoting, setPromoting] = useState<UserListItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: teachers, isLoading: teachersLoading } = useQuery({
    queryKey: ["admin-team-teachers"],
    queryFn: () => listUsers({ role: "TEACHER", page_size: 100, sort_by: "name", sort_dir: "asc" }),
  });

  const trimmedSearch = studentSearch.trim();
  const { data: studentResults, isLoading: searchLoading } = useQuery({
    queryKey: ["admin-team-student-search", trimmedSearch],
    queryFn: () => listUsers({ role: "STUDENT", search: trimmedSearch, page_size: 20 }),
    enabled: trimmedSearch.length >= 2,
  });

  const promoteMutation = useMutation({
    mutationFn: () => changeUserRole(promoting!.id, "TEACHER"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-team-teachers"] });
      queryClient.invalidateQueries({ queryKey: ["admin-team-student-search"] });
      setPromoting(null);
      setError(null);
    },
    onError: () => setError("Rolle konnte nicht geändert werden."),
  });

  const teacherColumns: DataTableColumn<UserListItem>[] = [
    {
      key: "avatar",
      header: "",
      className: "w-12",
      render: (item) => <Avatar src={item.profile_image ?? undefined} name={displayName(item)} size={32} />,
    },
    { key: "name", header: "Name", render: (item) => displayName(item) },
    {
      key: "user",
      header: "Login",
      render: (item) => (
        <div>
          <p className="font-medium">{item.username}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{item.email}</p>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            item.is_banned
              ? "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]"
              : item.is_active
                ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
                : "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.is_banned ? "Gesperrt" : item.is_active ? "Aktiv" : "Inaktiv"}
        </span>
      ),
    },
    {
      key: "since",
      header: "Registriert",
      render: (item) => new Date(item.created_at).toLocaleDateString("de-DE"),
    },
  ];

  const studentColumns: DataTableColumn<UserListItem>[] = [
    {
      key: "avatar",
      header: "",
      className: "w-12",
      render: (item) => <Avatar src={item.profile_image ?? undefined} name={displayName(item)} size={32} />,
    },
    { key: "name", header: "Name", render: (item) => displayName(item) },
    {
      key: "user",
      header: "Login",
      render: (item) => (
        <div>
          <p className="font-medium">{item.username}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{item.email}</p>
        </div>
      ),
    },
    {
      key: "action",
      header: "",
      className: "text-right",
      render: (item) => (
        <div className="flex justify-end">
          <AdminButton size="sm" variant="secondary" onClick={() => setPromoting(item)}>
            <UserPlus size={14} />
            Als Lehrer hinzufügen
          </AdminButton>
        </div>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader title="Team" description="Lehrer verwalten und neue Lehrer aus bestehenden Studenten ernennen." />

      <AdminCard className="mb-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
          Lehrer ({teachers?.total ?? 0})
        </h2>
        <DataTable
          columns={teacherColumns}
          data={teachers?.items}
          isLoading={teachersLoading}
          getRowId={(item) => item.id}
          emptyMessage="Noch keine Lehrer."
        />
      </AdminCard>

      <AdminCard>
        <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
          Student suchen
        </h2>
        <p className="mb-4 text-sm text-[var(--admin-text-secondary)]">
          Suche nach Nickname oder E-Mail, um einen Studenten zum Lehrer zu machen.
        </p>
        <div className="relative mb-4 max-w-md">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
          <AdminInput
            value={studentSearch}
            onChange={(e) => setStudentSearch(e.target.value)}
            placeholder="Nickname oder E-Mail..."
            className="pl-9"
          />
        </div>

        {trimmedSearch.length >= 2 && (
          <DataTable
            columns={studentColumns}
            data={studentResults?.items}
            isLoading={searchLoading}
            getRowId={(item) => item.id}
            emptyMessage="Keine Studenten gefunden."
          />
        )}
      </AdminCard>

      <FormDialog
        open={!!promoting}
        onOpenChange={(open) => !open && setPromoting(null)}
        title="Als Lehrer hinzufügen"
        description={
          promoting ? `"${displayName(promoting)}" (${promoting.email}) erhält die Rolle Lehrer.` : undefined
        }
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setPromoting(null)} disabled={promoteMutation.isPending}>
              Abbrechen
            </AdminButton>
            <AdminButton onClick={() => promoteMutation.mutate()} disabled={promoteMutation.isPending}>
              {promoteMutation.isPending ? "Wird gespeichert..." : "Bestätigen"}
            </AdminButton>
          </>
        }
      >
        <p className="text-sm text-[var(--admin-text-secondary)]">
          Der Nutzer erhält Zugriff auf das Lehrer-Panel (Schreiben-/Sprechen-Bewertung) und kann im Profilmenü
          jederzeit zwischen Student- und Lehrer-Panel wechseln.
        </p>
        {error && <p className="mt-2 text-sm text-[var(--admin-danger)]">{error}</p>}
      </FormDialog>
    </div>
  );
}
