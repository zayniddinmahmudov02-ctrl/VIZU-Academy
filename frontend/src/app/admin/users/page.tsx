"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDownAZ,
  ArrowUpAZ,
  Ban,
  ChevronLeft,
  ChevronRight,
  Circle,
  Crown,
  Key,
  Lock,
  ShieldOff,
  Search,
} from "lucide-react";

import {
  AdminButton,
  AdminCard,
  AdminInput,
  AdminLabel,
  AdminPageHeader,
  AdminSelect,
} from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import Avatar from "@/components/ui/avatar";
import { ALL_ROLES, UserListItem } from "@/features/admin/types/user.types";
import {
  banUser,
  changeUserRole,
  getUserDetail,
  grantPremium,
  listUsers,
  resetUserPassword,
  suspendUser,
  unbanUser,
  unsuspendUser,
} from "@/features/admin/services/users-service";

const PAGE_SIZE = 50;

function displayName(item: UserListItem): string {
  return [item.first_name, item.last_name].filter(Boolean).join(" ") || item.username;
}

function formatUsage(minutes: number): string {
  if (minutes <= 0) return "—";
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return hours > 0 ? `${hours} Std. ${rest} Min.` : `${rest} Min.`;
}

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [selected, setSelected] = useState<UserListItem | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users", page, search, role, sortDir],
    queryFn: () =>
      listUsers({
        page,
        page_size: PAGE_SIZE,
        search: search || undefined,
        role: role || undefined,
        sort_by: "name",
        sort_dir: sortDir,
      }),
  });

  const { data: detail } = useQuery({
    queryKey: ["admin-user-detail", selected?.id],
    queryFn: () => getUserDetail(selected!.id),
    enabled: !!selected,
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    queryClient.invalidateQueries({ queryKey: ["admin-user-detail"] });
  }

  const banMutation = useMutation({
    mutationFn: () => banUser(selected!.id, window.prompt("Grund für die Sperrung:") ?? ""),
    onSuccess: invalidate,
  });
  const unbanMutation = useMutation({ mutationFn: () => unbanUser(selected!.id), onSuccess: invalidate });
  const suspendMutation = useMutation({
    mutationFn: () => {
      const days = Number(window.prompt("Für wie viele Tage sperren?", "7") ?? "0");
      const reason = window.prompt("Grund:") ?? "";
      return suspendUser(selected!.id, days, reason);
    },
    onSuccess: invalidate,
  });
  const unsuspendMutation = useMutation({
    mutationFn: () => unsuspendUser(selected!.id),
    onSuccess: invalidate,
  });
  const premiumMutation = useMutation({
    mutationFn: () => {
      const days = Number(window.prompt("Premium für wie viele Tage gewähren?", "30") ?? "0");
      return grantPremium(selected!.id, days);
    },
    onSuccess: invalidate,
  });
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const resetPasswordMutation = useMutation({
    mutationFn: () => resetUserPassword(selected!.id),
    onSuccess: (res) => {
      setTempPassword(res.temporary_password);
      invalidate();
    },
  });
  const roleMutation = useMutation({
    mutationFn: (newRole: string) => changeUserRole(selected!.id, newRole),
    onSuccess: invalidate,
  });

  const columns: DataTableColumn<UserListItem>[] = [
    {
      key: "avatar",
      header: "",
      className: "w-12",
      render: (item) => <Avatar src={item.profile_image ?? undefined} name={displayName(item)} size={32} />,
    },
    { key: "first_name", header: "Vorname", render: (item) => item.first_name || "—" },
    { key: "last_name", header: "Nachname", render: (item) => item.last_name || "—" },
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
      key: "password",
      header: "Passwort",
      render: (item) => (
        <span className="inline-flex items-center gap-1 text-xs text-[var(--admin-text-muted)]">
          <Lock size={11} />
          {item.has_password ? "gesetzt" : "—"}
        </span>
      ),
    },
    {
      key: "online",
      header: "Status",
      render: (item) => (
        <span
          className={`inline-flex items-center gap-1.5 text-xs font-medium ${
            item.is_online ? "text-[var(--admin-accent)]" : "text-[var(--admin-text-muted)]"
          }`}
        >
          <Circle size={7} fill="currentColor" strokeWidth={0} />
          {item.is_online ? "Online" : "Offline"}
        </span>
      ),
    },
    {
      key: "last_login",
      header: "Letzter Login",
      render: (item) => (item.last_login ? new Date(item.last_login).toLocaleString("de-DE") : "—"),
    },
    {
      key: "usage",
      header: "Nutzungszeit",
      render: (item) => formatUsage(item.usage_minutes),
    },
    {
      key: "created_at",
      header: "Registriert",
      render: (item) => new Date(item.created_at).toLocaleDateString("de-DE"),
    },
    {
      key: "badges",
      header: "",
      render: (item) => (
        <div className="flex flex-wrap gap-1">
          {item.is_banned && (
            <span className="rounded-full bg-[var(--admin-danger)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-danger)]">
              Gesperrt
            </span>
          )}
          {item.is_suspended && (
            <span className="rounded-full bg-[var(--admin-warning)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-warning)]">
              Suspendiert
            </span>
          )}
          {item.is_premium && (
            <span className="rounded-full bg-[var(--admin-primary)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-primary)]">
              Premium
            </span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader title="Users" description="Nutzerverwaltung: Rollen, Sperrungen, Premium-Status." />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
          <AdminInput
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Suche nach Vorname, Nachname oder Login..."
            className="pl-9"
          />
        </div>
        <AdminSelect
          value={role}
          onChange={(e) => {
            setRole(e.target.value);
            setPage(1);
          }}
          className="w-48"
        >
          <option value="">Alle Rollen</option>
          {ALL_ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </AdminSelect>
        <AdminButton
          variant="secondary"
          onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
          aria-label="Sortierreihenfolge umschalten"
        >
          {sortDir === "asc" ? <ArrowDownAZ size={15} /> : <ArrowUpAZ size={15} />}
          Nachname, Vorname
        </AdminButton>
      </div>

      <DataTable
        columns={columns}
        data={data?.items}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={(item) => setSelected(item)}
        emptyMessage="Keine Nutzer gefunden."
      />

      {data && data.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
          <span>
            Seite {data.page} von {data.total_pages} ({data.total} Nutzer)
          </span>
          <div className="flex gap-2">
            <AdminButton
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              <ChevronLeft size={14} />
            </AdminButton>
            <AdminButton
              variant="secondary"
              size="sm"
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              <ChevronRight size={14} />
            </AdminButton>
          </div>
        </div>
      )}

      <FormDialog
        open={!!selected}
        onOpenChange={(open) => {
          if (!open) {
            setSelected(null);
            setTempPassword(null);
          }
        }}
        title={selected?.username ?? ""}
        description={selected?.email}
        size="lg"
      >
        {detail && (
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-3">
              <AdminCard className="p-3 text-center">
                <p className="text-lg font-bold text-[var(--admin-text-primary)]">
                  {detail.enrollments_count}
                </p>
                <p className="text-xs text-[var(--admin-text-muted)]">Kurse</p>
              </AdminCard>
              <AdminCard className="p-3 text-center">
                <p className="text-lg font-bold text-[var(--admin-text-primary)]">
                  {detail.certificates_count}
                </p>
                <p className="text-xs text-[var(--admin-text-muted)]">Zertifikate</p>
              </AdminCard>
              <AdminCard className="p-3 text-center">
                <p className="text-lg font-bold text-[var(--admin-text-primary)]">
                  {detail.payments_total.toLocaleString()}
                </p>
                <p className="text-xs text-[var(--admin-text-muted)]">Zahlungen</p>
              </AdminCard>
            </div>

            {tempPassword && (
              <div className="rounded-lg bg-[var(--admin-accent)]/10 p-3 text-sm text-[var(--admin-accent)]">
                Neues temporäres Passwort: <span className="font-mono font-bold">{tempPassword}</span>
              </div>
            )}

            <div>
              <AdminLabel>Rolle ändern</AdminLabel>
              <AdminSelect
                defaultValue={detail.role}
                onChange={(e) => roleMutation.mutate(e.target.value)}
              >
                {ALL_ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </AdminSelect>
            </div>

            <div className="flex flex-wrap gap-2">
              {detail.is_banned ? (
                <AdminButton variant="secondary" size="sm" onClick={() => unbanMutation.mutate()}>
                  <ShieldOff size={13} />
                  Entsperren
                </AdminButton>
              ) : (
                <AdminButton variant="danger" size="sm" onClick={() => banMutation.mutate()}>
                  <Ban size={13} />
                  Sperren
                </AdminButton>
              )}

              {detail.is_suspended ? (
                <AdminButton variant="secondary" size="sm" onClick={() => unsuspendMutation.mutate()}>
                  Suspendierung aufheben
                </AdminButton>
              ) : (
                <AdminButton variant="secondary" size="sm" onClick={() => suspendMutation.mutate()}>
                  Suspendieren
                </AdminButton>
              )}

              <AdminButton variant="secondary" size="sm" onClick={() => premiumMutation.mutate()}>
                <Crown size={13} />
                Premium gewähren
              </AdminButton>

              <AdminButton variant="secondary" size="sm" onClick={() => resetPasswordMutation.mutate()}>
                <Key size={13} />
                Passwort zurücksetzen
              </AdminButton>
            </div>
          </div>
        )}
      </FormDialog>
    </div>
  );
}
