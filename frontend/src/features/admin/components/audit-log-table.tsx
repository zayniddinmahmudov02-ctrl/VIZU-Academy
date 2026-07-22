import type { AuditLogResponse } from "../types/user";
import PaginationBar from "./pagination-bar";

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(
    new Date(value),
  );
}

interface Props {
  log: AuditLogResponse;
  page: number;
  onPageChange: (page: number) => void;
}

export default function AuditLogTable({ log, page, onPageChange }: Props) {
  return (
    <div className="admin-glass rounded-2xl p-5">
      <p className="mb-4 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Audit Log</p>

      <div className="space-y-1">
        {log.items.length === 0 ? (
          <p className="py-6 text-center text-xs text-[var(--admin-text-muted)]">No admin actions recorded yet.</p>
        ) : (
          log.items.map((entry) => (
            <div key={entry.id} className="rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white">{entry.action.replace(/_/g, " ")}</span>
                <span className="text-[11px] text-[var(--admin-text-muted)]">{formatDateTime(entry.createdAt)}</span>
              </div>
              <p className="mt-0.5 text-[11px] text-[var(--admin-text-muted)]">
                By {entry.actorEmail ?? "Unknown"}
                {entry.details ? ` — ${entry.details}` : ""}
              </p>
            </div>
          ))
        )}
      </div>

      <div className="mt-4">
        <PaginationBar page={page} totalPages={log.totalPages} total={log.total} onPageChange={onPageChange} />
      </div>
    </div>
  );
}
