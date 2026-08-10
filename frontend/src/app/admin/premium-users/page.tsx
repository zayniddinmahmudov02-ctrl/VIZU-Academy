"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

import { AdminInput, AdminPageHeader } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import Avatar from "@/components/ui/avatar";
import { listUsers } from "@/features/admin/services/users-service";
import type { UserListItem } from "@/features/admin/types/user.types";

const PAGE_SIZE = 50;

function displayName(item: UserListItem): string {
  return [item.first_name, item.last_name].filter(Boolean).join(" ") || item.username;
}

export default function PremiumUsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  // Reuses the existing subscription/premium architecture — User.premium_until
  // (already the source of truth for premium status on the student side,
  // e.g. vizu-pay) filtered server-side via the existing `status=premium`
  // AdminUsersService filter. No new user/subscription entity created.
  const { data, isLoading } = useQuery({
    queryKey: ["admin-premium-users", page, search],
    queryFn: () =>
      listUsers({
        page,
        page_size: PAGE_SIZE,
        search: search || undefined,
        status: "premium",
        sort_by: "premium_until",
        sort_dir: "asc",
      }),
  });

  const columns: DataTableColumn<UserListItem>[] = [
    {
      key: "avatar",
      header: "",
      className: "w-12",
      render: (item) => <Avatar src={item.profile_image ?? undefined} name={displayName(item)} size={32} />,
    },
    {
      key: "user",
      header: "Nutzer",
      render: (item) => (
        <div>
          <p className="font-medium">{displayName(item)}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{item.email}</p>
        </div>
      ),
    },
    {
      key: "premium_until",
      header: "Premium bis",
      render: (item) =>
        item.premium_until ? new Date(item.premium_until).toLocaleDateString("de-DE") : "—",
    },
    {
      key: "last_login",
      header: "Letzter Login",
      render: (item) => (item.last_login ? new Date(item.last_login).toLocaleDateString("de-DE") : "—"),
    },
    {
      key: "manage",
      header: "",
      render: () => (
        <Link
          href="/admin/users"
          className="text-xs font-medium text-[var(--admin-primary)] hover:underline"
        >
          In Users verwalten →
        </Link>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader
        title="Premium-Users"
        description="Nutzer mit aktivem Premium-Status (aus dem bestehenden Abo-/Zahlungssystem)."
      />

      <div className="mb-4 relative max-w-md">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
        <AdminInput
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="Suche nach Name oder Login..."
          className="pl-9"
        />
      </div>

      <DataTable
        columns={columns}
        data={data?.items}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage="Keine Premium-Nutzer gefunden."
      />

      {data && data.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
          <span>
            Seite {data.page} von {data.total_pages} ({data.total} Premium-Nutzer)
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--admin-card)] ring-1 ring-[var(--admin-border-strong)] disabled:opacity-40"
            >
              <ChevronLeft size={14} />
            </button>
            <button
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--admin-card)] ring-1 ring-[var(--admin-border-strong)] disabled:opacity-40"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
