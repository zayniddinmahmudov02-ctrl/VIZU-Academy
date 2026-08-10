import type { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  title: string;
  description: string;
}

/** A clean, centered empty state for admin sections that have no
 * functionality yet (VIZU-MOCK, Homeworks) — intentionally not wired to
 * any data source, so it never risks rendering demo/placeholder content. */
export default function AdminEmptySection({ icon: Icon, title, description }: Props) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl bg-[var(--admin-card)] px-6 py-20 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--admin-primary)]/10 text-[var(--admin-primary)]">
        <Icon size={24} />
      </div>
      <h2 className="mt-4 text-base font-semibold text-[var(--admin-text-primary)]">{title}</h2>
      <p className="mt-1.5 max-w-sm text-sm text-[var(--admin-text-muted)]">{description}</p>
    </div>
  );
}
