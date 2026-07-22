import type { ReactNode } from "react";

interface Props {
  title: string;
  children: ReactNode;
  isEmpty: boolean;
  emptyLabel: string;
}

export default function ListCard({ title, children, isEmpty, emptyLabel }: Props) {
  return (
    <div className="admin-glass rounded-2xl p-5 shadow-[var(--admin-shadow-card)] sm:p-6">
      <p className="text-sm font-bold text-white">{title}</p>

      <div className="mt-4 space-y-1">
        {isEmpty ? (
          <p className="py-6 text-center text-xs text-[var(--admin-text-muted)]">{emptyLabel}</p>
        ) : (
          children
        )}
      </div>
    </div>
  );
}
