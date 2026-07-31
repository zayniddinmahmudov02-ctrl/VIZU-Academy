"use client";

import { Ban, Crown, KeyRound, LogIn, UserCheck, PauseCircle, PlayCircle } from "lucide-react";

import type { AdminUserDetail } from "../types/user";

const ROLE_OPTIONS = [
  "SUPER_ADMIN",
  "ADMIN",
  "CONTENT_MANAGER",
  "PAYMENT_MANAGER",
  "SUPPORT",
  "TEACHER",
  "STUDENT",
];

interface Props {
  user: AdminUserDetail;
  disabled: boolean;
  onBan: () => void;
  onUnban: () => void;
  onSuspend: () => void;
  onUnsuspend: () => void;
  onGrantPremium: () => void;
  onExtendSubscription: () => void;
  onResetPassword: () => void;
  onImpersonate: () => void;
  onRoleChange: (role: string) => void;
}

function ActionButton({
  icon,
  label,
  onClick,
  disabled,
  tone = "neutral",
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  tone?: "neutral" | "danger" | "primary";
}) {
  const toneClasses =
    tone === "danger"
      ? "hover:border-[#ef4444]/50 hover:text-[#ef4444]"
      : tone === "primary"
        ? "hover:border-[var(--admin-primary)]/50 hover:text-[var(--admin-primary)]"
        : "hover:border-white/20 hover:text-white";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center gap-2 rounded-xl border border-[var(--admin-border)] px-3.5 py-2.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors disabled:opacity-40 ${toneClasses}`}
    >
      {icon}
      {label}
    </button>
  );
}

export default function ProfileActions({
  user,
  disabled,
  onBan,
  onUnban,
  onSuspend,
  onUnsuspend,
  onGrantPremium,
  onExtendSubscription,
  onResetPassword,
  onImpersonate,
  onRoleChange,
}: Props) {
  return (
    <div className="admin-glass rounded-2xl p-5">
      <p className="mb-3 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Actions</p>

      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="user-role-select" className="text-xs font-semibold text-[var(--admin-text-secondary)]">
          Role
        </label>
        <select
          id="user-role-select"
          value={user.role}
          disabled={disabled}
          onChange={(event) => onRoleChange(event.target.value)}
          className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] px-3 py-2 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50 disabled:opacity-40"
        >
          {ROLE_OPTIONS.map((role) => (
            <option key={role} value={role} className="bg-[#111827]">
              {role.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-wrap gap-2">
        {user.isBanned ? (
          <ActionButton icon={<UserCheck size={14} />} label="Unban" onClick={onUnban} disabled={disabled} tone="primary" />
        ) : (
          <ActionButton icon={<Ban size={14} />} label="Ban User" onClick={onBan} disabled={disabled} tone="danger" />
        )}

        {user.isSuspended ? (
          <ActionButton icon={<PlayCircle size={14} />} label="Unsuspend" onClick={onUnsuspend} disabled={disabled} tone="primary" />
        ) : (
          <ActionButton icon={<PauseCircle size={14} />} label="Suspend" onClick={onSuspend} disabled={disabled} />
        )}

        <ActionButton icon={<Crown size={14} />} label="Grant Premium" onClick={onGrantPremium} disabled={disabled} tone="primary" />
        <ActionButton icon={<Crown size={14} />} label="Extend Subscription" onClick={onExtendSubscription} disabled={disabled} />
        <ActionButton icon={<KeyRound size={14} />} label="Reset Password" onClick={onResetPassword} disabled={disabled} />
        <ActionButton icon={<LogIn size={14} />} label="Login As User" onClick={onImpersonate} disabled={disabled} tone="danger" />
      </div>
    </div>
  );
}
