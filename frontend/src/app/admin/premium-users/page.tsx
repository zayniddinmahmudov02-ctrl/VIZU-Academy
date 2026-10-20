"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

import { AdminCard, AdminInput, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import Avatar from "@/components/ui/avatar";
import { CoursePurchaseBadges, formatPurchaseDate } from "@/features/admin/components/course-purchase-badges";
import { listUsers } from "@/features/admin/services/users-service";
import type { UserListItem } from "@/features/admin/types/user.types";

const PAGE_SIZE = 50;

type Filter = "paying" | "buyer" | "premium";

const FILTER_LABELS: Record<Filter, string> = {
  paying: "Alle zahlenden Nutzer",
  buyer: "Nur Kurskäufer",
  premium: "Nur Premium (Abo)",
};

function displayName(item: UserListItem): string {
  return [item.first_name, item.last_name].filter(Boolean).join(" ") || item.username;
}

function lastPurchaseAt(item: UserListItem): string | null {
  return item.course_purchases?.[0]?.purchased_at ?? null;
}

export default function PremiumUsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("paying");

  // Reuses the users list: `paying` = active legacy Premium (User.premium_until)
  // OR at least one APPROVED course order — the shared purchase rule of
  // backend purchases.py. Pending / rejected orders never make a user appear here.
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-premium-users", page, search, filter],
    queryFn: () =>
      listUsers({
        page,
        page_size: PAGE_SIZE,
        search: search || undefined,
        status: filter,
        sort_by: filter === "premium" ? "premium_until" : "last_purchase",
        sort_dir: filter === "premium" ? "asc" : "desc",
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
      key: "courses",
      header: "Kurs / Level",
      render: (item) =>
        (item.course_purchases ?? []).length > 0 ? (
          <div className="space-y-0.5">
            <CoursePurchaseBadges purchases={item.course_purchases} />
            <p className="text-[11px] text-[var(--admin-text-muted)]">
              {Array.from(new Set(item.course_purchases.flatMap((p) => p.levels))).join(", ")}
            </p>
          </div>
        ) : (
          <span className="text-xs text-[var(--admin-text-muted)]">—</span>
        ),
    },
    {
      key: "purchased_at",
      header: "Kaufdatum",
      render: (item) => formatPurchaseDate(lastPurchaseAt(item)),
    },
    {
      key: "payment_status",
      header: "Zahlungsstatus",
      render: (item) => (
        <div className="flex flex-wrap gap-1">
          {(item.course_purchases ?? []).length > 0 && (
            <span className="rounded-full bg-[var(--admin-accent)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-accent)]">
              Bestätigt
            </span>
          )}
          {item.is_premium && (
            <span className="rounded-full bg-[var(--admin-primary)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-primary)]">
              Premium aktiv
            </span>
          )}
          <CoursePurchaseBadges purchases={[]} pendingOrders={item.pending_orders ?? 0} />
        </div>
      ),
    },
    {
      key: "premium_until",
      header: "Premium bis",
      render: (item) =>
        item.is_premium && item.premium_until ? new Date(item.premium_until).toLocaleDateString("de-DE") : "—",
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
        <Link href="/admin/users" className="text-xs font-medium text-[var(--admin-primary)] hover:underline">
          In Users verwalten →
        </Link>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader
        title="Premium-Users"
        description="Nutzer mit aktivem Premium oder einem bestätigten Kurskauf. Offene oder abgelehnte Bestellungen zählen nicht."
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-[220px] max-w-md flex-1">
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
        <AdminSelect
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value as Filter);
            setPage(1);
          }}
          className="w-56"
          aria-label="Filter"
        >
          {(Object.keys(FILTER_LABELS) as Filter[]).map((f) => (
            <option key={f} value={f}>
              {FILTER_LABELS[f]}
            </option>
          ))}
        </AdminSelect>
      </div>

      {isError ? (
        <AdminCard>
          <p className="text-sm text-[var(--admin-danger)]">Nutzer konnten nicht geladen werden.</p>
          <button onClick={() => refetch()} className="mt-1 text-xs text-[var(--admin-primary)] hover:underline">
            Erneut versuchen
          </button>
        </AdminCard>
      ) : (
        <DataTable
          columns={columns}
          data={data?.items}
          isLoading={isLoading}
          getRowId={(item) => item.id}
          emptyMessage="Keine zahlenden Nutzer gefunden."
        />
      )}

      {data && data.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
          <span>
            Seite {data.page} von {data.total_pages} ({data.total} Nutzer)
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
      {data && data.total_pages <= 1 && data.total > 0 && (
        <p className="mt-3 text-xs text-[var(--admin-text-muted)]">{data.total} Nutzer</p>
      )}
    </div>
  );
}
