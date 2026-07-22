import { Award, CreditCard, LogIn, UserPlus, BookOpen, Activity } from "lucide-react";

import type { ActivityTimelineItem } from "../types/user";

const ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  registration: UserPlus,
  login: LogIn,
  payment: CreditCard,
  certificate: Award,
  enrollment: BookOpen,
};

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

export default function ActivityTimeline({ items }: { items: ActivityTimelineItem[] }) {
  return (
    <div className="admin-glass rounded-2xl p-5">
      <p className="mb-4 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Activity Timeline</p>

      <div className="max-h-96 space-y-1 overflow-y-auto">
        {items.length === 0 ? (
          <p className="py-6 text-center text-xs text-[var(--admin-text-muted)]">No activity yet.</p>
        ) : (
          items.map((item, index) => {
            const Icon = ICONS[item.type] ?? Activity;
            return (
              <div key={index} className="flex items-center gap-3 rounded-xl px-2 py-2 hover:bg-white/[0.03]">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/5 text-[var(--admin-text-secondary)]">
                  <Icon size={14} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-white">{item.title}</p>
                </div>
                <span className="shrink-0 text-[10px] text-[var(--admin-text-muted)]">{formatDateTime(item.timestamp)}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
