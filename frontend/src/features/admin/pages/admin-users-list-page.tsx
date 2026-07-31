"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Users as UsersIcon } from "lucide-react";

import { useAdminUsersList } from "../hooks/use-admin-users-list";
import { exportUsersCsv, exportUsersXlsx } from "../services/users-service";
import UsersFiltersBar from "../components/users-filters-bar";
import UsersTable from "../components/users-table";
import PaginationBar from "../components/pagination-bar";

const STAFF_ROLE_OPTIONS = ["SUPER_ADMIN", "ADMIN", "CONTENT_MANAGER", "PAYMENT_MANAGER", "SUPPORT", "TEACHER"];

interface Props {
  /** Restricts the list to staff roles only and swaps the header/icon —
   *  powers the "Admins" panel at /admin/admins, reusing everything else
   *  (search/filter/sort/pagination/export) as-is. */
  staffOnly?: boolean;
}

export default function AdminUsersListPage({ staffOnly = false }: Props) {
  const { query, data, loading, error, setSearch, setRole, setStatus, setPage, setSort } = useAdminUsersList({
    staffOnly,
  });

  const [searchInput, setSearchInput] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setSearch(searchInput), 350);
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput]);

  async function handleExport(format: "csv" | "xlsx") {
    setExporting(true);
    try {
      if (format === "csv") {
        await exportUsersCsv(query);
      } else {
        await exportUsersXlsx(query);
      }
    } catch (err) {
      console.warn("Export failed:", err);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="admin-glass flex flex-wrap items-center justify-between gap-4 rounded-2xl p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-white">
            {staffOnly ? <ShieldCheck size={20} /> : <UsersIcon size={20} />}
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">{staffOnly ? "Admins" : "Users"}</h1>
            <p className="text-xs text-[var(--admin-text-muted)]">
              {data ? `${data.total} ${staffOnly ? "staff accounts" : "registered users"}` : "Loading…"}
            </p>
          </div>
        </div>
      </div>

      <UsersFiltersBar
        search={searchInput}
        onSearchChange={setSearchInput}
        role={query.role}
        onRoleChange={setRole}
        status={query.status}
        onStatusChange={setStatus}
        onExportCsv={() => handleExport("csv")}
        onExportXlsx={() => handleExport("xlsx")}
        exporting={exporting}
        roleOptions={staffOnly ? STAFF_ROLE_OPTIONS : undefined}
      />

      {error ? (
        <div className="admin-glass rounded-2xl p-8 text-center">
          <p className="text-sm font-semibold text-white">Could not load users</p>
          <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Check that the backend is running and reachable.</p>
        </div>
      ) : (
        <>
          <UsersTable items={data?.items ?? []} loading={loading} sortBy={query.sortBy} sortDir={query.sortDir} onSort={setSort} />
          {data && <PaginationBar page={data.page} totalPages={data.totalPages} total={data.total} onPageChange={setPage} />}
        </>
      )}
    </div>
  );
}
