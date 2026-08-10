"use client";

import { Camera, Mail } from "lucide-react";

import Avatar from "@/components/ui/avatar";
import Badge from "@/components/ui/badge";
import type { CurrentUser } from "@/features/auth/types/user";
import { useTranslation } from "@/lib/i18n/use-translation";

import { getAccountStatus } from "../utils/account-status";

const STATUS_VARIANT = {
  active: "success",
  banned: "danger",
  suspended: "warning",
  inactive: "neutral",
} as const;

const STATUS_KEY = {
  active: "profile.statusActive",
  banned: "profile.statusBanned",
  suspended: "profile.statusSuspended",
  inactive: "profile.statusInactive",
} as const;

interface Props {
  user: CurrentUser;
  onPickPhoto: () => void;
}

function displayName(user: CurrentUser): string {
  const full = [user.firstName, user.lastName].filter(Boolean).join(" ").trim();
  return full || user.username;
}

export default function ProfileHeader({ user, onPickPhoto }: Props) {
  const { t } = useTranslation();
  const status = getAccountStatus(user);

  return (
    <section className="relative overflow-hidden rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-8 text-white shadow-[var(--shadow-lg)]">
      <div className="flex flex-wrap items-center gap-5">
        <button
          type="button"
          onClick={onPickPhoto}
          className="group relative rounded-full outline-none focus-visible:ring-2 focus-visible:ring-white/60"
          aria-label={t("profile.photo")}
        >
          <Avatar src={user.profileImage ?? undefined} name={displayName(user)} size={88} />
          <span className="absolute inset-0 flex items-center justify-center rounded-full bg-black/0 text-white opacity-0 transition-all duration-200 group-hover:bg-black/40 group-hover:opacity-100">
            <Camera size={22} />
          </span>
        </button>

        <div className="min-w-0">
          <h1 className="truncate text-2xl font-bold">{displayName(user)}</h1>
          <p className="mt-1 flex items-center gap-2 text-white/80">
            <Mail size={15} /> {user.email}
          </p>
          <div className="mt-3">
            <Badge variant={STATUS_VARIANT[status]} className="bg-white/15 text-white">
              {t(STATUS_KEY[status])}
            </Badge>
          </div>
        </div>
      </div>
    </section>
  );
}
