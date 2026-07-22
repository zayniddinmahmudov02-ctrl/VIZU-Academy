import { CheckCircle2, XCircle } from "lucide-react";

import type { LoginHistoryResponse } from "../types/user";
import PaginationBar from "./pagination-bar";

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(
    new Date(value),
  );
}

interface Props {
  history: LoginHistoryResponse;
  page: number;
  onPageChange: (page: number) => void;
}

export default function LoginHistoryTable({ history, page, onPageChange }: Props) {
  return (
    <div className="admin-glass rounded-2xl p-5">
      <p className="mb-4 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Login History</p>

      <div className="space-y-1">
        {history.items.length === 0 ? (
          <p className="py-6 text-center text-xs text-[var(--admin-text-muted)]">No login attempts recorded yet.</p>
        ) : (
          history.items.map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div className="flex items-center gap-2.5">
                {item.success ? (
                  <CheckCircle2 size={14} className="text-[#22c55e]" />
                ) : (
                  <XCircle size={14} className="text-[#ef4444]" />
                )}
                <div>
                  <p className="text-white">
                    {item.device} · {item.browser} · {item.os}
                  </p>
                  <p className="text-[11px] text-[var(--admin-text-muted)]">{item.ipAddress ?? "Unknown IP"}</p>
                </div>
              </div>
              <span className="shrink-0 text-[11px] text-[var(--admin-text-muted)]">{formatDateTime(item.createdAt)}</span>
            </div>
          ))
        )}
      </div>

      <div className="mt-4">
        <PaginationBar page={page} totalPages={history.totalPages} total={history.total} onPageChange={onPageChange} />
      </div>
    </div>
  );
}
