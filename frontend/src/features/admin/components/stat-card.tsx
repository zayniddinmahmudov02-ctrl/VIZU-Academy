import type { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string;
  icon: LucideIcon;
  gradient: string;
}

export default function StatCard({ label, value, icon: Icon, gradient }: Props) {
  return (
    <div className="admin-glass rounded-2xl p-5 shadow-[var(--admin-shadow-card)] transition-transform duration-200 hover:-translate-y-0.5">
      <div className="flex items-center justify-between">
        <div
          className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-md ${gradient}`}
        >
          <Icon size={20} />
        </div>
      </div>

      <p className="mt-4 text-2xl font-extrabold tracking-tight text-white">{value}</p>
      <p className="mt-1 text-xs font-medium text-[var(--admin-text-secondary)]">{label}</p>
    </div>
  );
}
