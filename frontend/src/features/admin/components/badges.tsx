interface BadgeProps {
  label: string;
  tone?: "neutral" | "success" | "warning" | "danger" | "primary";
}

const TONE_CLASSES: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "bg-white/5 text-[var(--admin-text-secondary)] ring-white/10",
  success: "bg-[#22c55e]/10 text-[#22c55e] ring-[#22c55e]/30",
  warning: "bg-[#f59e0b]/10 text-[#f59e0b] ring-[#f59e0b]/30",
  danger: "bg-[#ef4444]/10 text-[#ef4444] ring-[#ef4444]/30",
  primary: "bg-[var(--admin-primary)]/10 text-[var(--admin-primary)] ring-[var(--admin-primary)]/30",
};

export function Badge({ label, tone = "neutral" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset ${TONE_CLASSES[tone]}`}
    >
      {label}
    </span>
  );
}

export function RoleBadge({ role }: { role: string }) {
  const tone: BadgeProps["tone"] = role === "SUPER_ADMIN" || role === "ADMIN" ? "primary" : "neutral";
  return <Badge label={role.replace(/_/g, " ")} tone={tone} />;
}

export function UserStatusBadges({
  isBanned,
  isSuspended,
  isPremium,
}: {
  isBanned: boolean;
  isSuspended: boolean;
  isPremium: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {isBanned && <Badge label="Banned" tone="danger" />}
      {isSuspended && <Badge label="Suspended" tone="warning" />}
      {isPremium ? <Badge label="Premium" tone="success" /> : <Badge label="Trial" tone="neutral" />}
    </div>
  );
}
