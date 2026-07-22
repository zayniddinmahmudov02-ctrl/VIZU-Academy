"use client";

import type { ReactNode } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

export interface DataTableColumn<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render: (row: T) => ReactNode;
}

interface Props<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  getRowKey: (row: T) => string;
  loading: boolean;
  loadingLabel?: string;
  emptyLabel: string;
  sortBy?: string;
  sortDir?: "asc" | "desc";
  onSort?: (key: string) => void;
  onRowClick?: (row: T) => void;
  minWidth?: string;
}

/** Shared admin table shell — header/sort/loading/empty/row rendering in
 *  one place. Individual modules only ever define columns + data. */
export default function DataTable<T>({
  columns,
  rows,
  getRowKey,
  loading,
  loadingLabel = "Loading…",
  emptyLabel,
  sortBy,
  sortDir,
  onSort,
  onRowClick,
  minWidth = "800px",
}: Props<T>) {
  return (
    <div className="admin-glass overflow-hidden rounded-2xl">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm" style={{ minWidth }}>
          <thead>
            <tr className="border-b border-[var(--admin-border)]">
              {columns.map((col) => (
                <th key={col.key} className="px-4 py-3.5 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
                  {col.sortable && onSort ? (
                    <button
                      type="button"
                      onClick={() => onSort(col.key)}
                      className="flex items-center gap-1.5 transition-colors hover:text-white"
                    >
                      {col.label}
                      {sortBy === col.key ? (
                        sortDir === "asc" ? (
                          <ArrowUp size={12} />
                        ) : (
                          <ArrowDown size={12} />
                        )
                      ) : (
                        <ArrowUpDown size={12} className="opacity-40" />
                      )}
                    </button>
                  ) : (
                    col.label
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={columns.length} className="px-4 py-10 text-center text-[var(--admin-text-muted)]">
                  {loadingLabel}
                </td>
              </tr>
            )}

            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-4 py-10 text-center text-[var(--admin-text-muted)]">
                  {emptyLabel}
                </td>
              </tr>
            )}

            {!loading &&
              rows.map((row) => (
                <tr
                  key={getRowKey(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={`border-b border-[var(--admin-border)] transition-colors last:border-0 hover:bg-white/[0.03] ${
                    onRowClick ? "cursor-pointer" : ""
                  }`}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3.5">
                      {col.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
