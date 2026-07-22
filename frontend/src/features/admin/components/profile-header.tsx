"use client";

import { X } from "lucide-react";

import type { AdminUserDetail } from "../types/user";
import { RoleBadge, UserStatusBadges, Badge } from "./badges";

interface Props {
  user: AdminUserDetail;
  onAddTag: () => void;
  onRemoveTag: (tagId: string) => void;
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

export default function ProfileHeader({ user, onAddTag, onRemoveTag }: Props) {
  return (
    <div className="admin-glass rounded-2xl p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-lg font-bold text-white">
            {user.username.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">{user.username}</h1>
            <p className="text-sm text-[var(--admin-text-muted)]">{user.email}</p>
            <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Joined {formatDate(user.createdAt)}</p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <RoleBadge role={user.role} />
          <UserStatusBadges isBanned={user.isBanned} isSuspended={user.isSuspended} isPremium={user.isPremium} />
        </div>
      </div>

      {user.isBanned && user.banReason && (
        <p className="mt-4 rounded-xl bg-[#ef4444]/10 px-3 py-2 text-xs text-[#ef4444]">Ban reason: {user.banReason}</p>
      )}
      {user.isSuspended && user.suspendReason && (
        <p className="mt-4 rounded-xl bg-[#f59e0b]/10 px-3 py-2 text-xs text-[#f59e0b]">
          Suspended until {formatDate(user.suspendedUntil)} — {user.suspendReason}
        </p>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2">
        {user.tags.map((tag) => (
          <span
            key={tag.id}
            className="flex items-center gap-1.5 rounded-full bg-[var(--admin-primary)]/10 px-2.5 py-1 text-[11px] font-semibold text-[var(--admin-primary)] ring-1 ring-inset ring-[var(--admin-primary)]/30"
          >
            {tag.label}
            <button type="button" onClick={() => onRemoveTag(tag.id)} className="text-[var(--admin-primary)]/70 hover:text-white">
              <X size={11} />
            </button>
          </span>
        ))}
        <button
          type="button"
          onClick={onAddTag}
          className="rounded-full border border-dashed border-[var(--admin-border)] px-2.5 py-1 text-[11px] font-semibold text-[var(--admin-text-muted)] transition-colors hover:border-[var(--admin-primary)]/50 hover:text-white"
        >
          + Add tag
        </button>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-white/[0.03] p-3 text-center">
          <p className="text-lg font-bold text-white">{user.enrollmentsCount}</p>
          <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">Enrollments</p>
        </div>
        <div className="rounded-xl bg-white/[0.03] p-3 text-center">
          <p className="text-lg font-bold text-white">{user.certificatesCount}</p>
          <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">Certificates</p>
        </div>
        <div className="rounded-xl bg-white/[0.03] p-3 text-center">
          <p className="text-lg font-bold text-white">{new Intl.NumberFormat("de-DE").format(user.paymentsTotal)} UZS</p>
          <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">Total Paid</p>
        </div>
      </div>
    </div>
  );
}
