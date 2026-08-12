"use client";

import { ReactNode } from "react";
import { Pencil, Trash2 } from "lucide-react";

import { cn } from "@/lib/utils";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (item: T) => ReactNode;
  className?: string;
}

interface Props<T> {
  columns: DataTableColumn<T>[];
  data: T[] | undefined;
  isLoading?: boolean;
  getRowId: (item: T) => string;
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
  emptyMessage?: string;
}

function AdminSpinner() {
  return (
    <div className="flex items-center justify-center py-10">
      <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-[var(--admin-border-strong)] border-t-[var(--admin-primary)]" />
    </div>
  );
}

export default function DataTable<T>({
  columns,
  data,
  isLoading,
  getRowId,
  onEdit,
  onDelete,
  emptyMessage = "Keine Einträge vorhanden.",
}: Props<T>) {
  const hasActions = !!onEdit || !!onDelete;

  return (
    <div className="overflow-hidden rounded-2xl bg-[var(--admin-card)] shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--admin-border)] bg-white/[0.02]">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "px-4 py-3 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]",
                    col.className,
                  )}
                >
                  {col.header}
                </th>
              ))}
              {hasActions && (
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
                  Aktionen
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={columns.length + (hasActions ? 1 : 0)}>
                  <AdminSpinner />
                </td>
              </tr>
            )}

            {!isLoading && (!data || data.length === 0) && (
              <tr>
                <td
                  colSpan={columns.length + (hasActions ? 1 : 0)}
                  className="px-4 py-10 text-center text-sm text-[var(--admin-text-muted)]"
                >
                  {emptyMessage}
                </td>
              </tr>
            )}

            {!isLoading &&
              data?.map((item) => (
                <tr
                  key={getRowId(item)}
                  className="border-b border-[var(--admin-border)] last:border-0 hover:bg-white/[0.03]"
                >
                  {columns.map((col) => (
                    <td key={col.key} className={cn("px-4 py-3 text-[var(--admin-text-primary)]", col.className)}>
                      {col.render(item)}
                    </td>
                  ))}
                  {hasActions && (
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1.5">
                        {onEdit && (
                          <button
                            onClick={() => onEdit(item)}
                            aria-label="Bearbeiten"
                            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-primary)]/10 hover:text-[var(--admin-primary)]"
                          >
                            <Pencil size={15} />
                          </button>
                        )}
                        {onDelete && (
                          <button
                            onClick={() => onDelete(item)}
                            aria-label="Löschen"
                            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
                          >
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
