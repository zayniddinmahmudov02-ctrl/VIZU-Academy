"use client";

import { useRouter } from "next/navigation";

import type { AdminUserListItem } from "../types/user";
import { RoleBadge, UserStatusBadges, Badge } from "./badges";
import DataTable, { type DataTableColumn } from "./data-table";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(
    new Date(value),
  );
}

interface Props {
  items: AdminUserListItem[];
  loading: boolean;
  sortBy?: string;
  sortDir?: "asc" | "desc";
  onSort: (key: string) => void;
}

export default function UsersTable({ items, loading, sortBy, sortDir, onSort }: Props) {
  const router = useRouter();

  const columns: DataTableColumn<AdminUserListItem>[] = [
    {
      key: "username",
      label: "User",
      sortable: true,
      render: (user) => (
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-white">{user.username}</p>
          <p className="truncate text-xs text-[var(--admin-text-muted)]">{user.email}</p>
        </div>
      ),
    },
    { key: "role", label: "Role", sortable: true, render: (user) => <RoleBadge role={user.role} /> },
    {
      key: "status",
      label: "Status",
      render: (user) => <UserStatusBadges isBanned={user.isBanned} isSuspended={user.isSuspended} isPremium={user.isPremium} />,
    },
    {
      key: "tags",
      label: "Tags",
      render: (user) => (
        <div className="flex flex-wrap gap-1">
          {user.tags.length === 0 ? (
            <span className="text-xs text-[var(--admin-text-muted)]">—</span>
          ) : (
            user.tags.map((tag) => <Badge key={tag.id} label={tag.label} tone="primary" />)
          )}
        </div>
      ),
    },
    {
      key: "last_login",
      label: "Last Login",
      sortable: true,
      render: (user) => <span className="text-xs text-[var(--admin-text-secondary)]">{formatDate(user.lastLogin)}</span>,
    },
    {
      key: "created_at",
      label: "Joined",
      sortable: true,
      render: (user) => <span className="text-xs text-[var(--admin-text-secondary)]">{formatDate(user.createdAt)}</span>,
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={items}
      getRowKey={(user) => user.id}
      loading={loading}
      loadingLabel="Loading users…"
      emptyLabel="No users match these filters."
      sortBy={sortBy}
      sortDir={sortDir}
      onSort={onSort}
      onRowClick={(user) => router.push(`/admin/users/${user.id}`)}
      minWidth="880px"
    />
  );
}
