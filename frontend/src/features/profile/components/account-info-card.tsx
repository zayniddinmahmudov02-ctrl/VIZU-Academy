"use client";

import { Info } from "lucide-react";

import Badge from "@/components/ui/badge";
import { localeFor } from "@/features/calendar/utils/date-helpers";
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
}

export default function AccountInfoCard({ user }: Props) {
  const { t, language } = useTranslation();
  const status = getAccountStatus(user);

  const createdAt = new Intl.DateTimeFormat(localeFor(language), {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(user.createdAt));

  return (
    <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <h2 className="flex items-center gap-2 text-lg font-bold text-text-primary">
        <Info size={18} className="text-accent-blue" />
        {t("profile.accountInfo")}
      </h2>

      <dl className="mt-5 space-y-4 text-sm">
        <div className="flex items-center justify-between border-b border-surface-border pb-3">
          <dt className="text-text-secondary">{t("profile.memberSince")}</dt>
          <dd className="font-medium text-text-primary">{createdAt}</dd>
        </div>
        <div className="flex items-center justify-between pb-1">
          <dt className="text-text-secondary">{t("profile.accountStatus")}</dt>
          <dd>
            <Badge variant={STATUS_VARIANT[status]}>{t(STATUS_KEY[status])}</Badge>
          </dd>
        </div>
      </dl>
    </section>
  );
}
