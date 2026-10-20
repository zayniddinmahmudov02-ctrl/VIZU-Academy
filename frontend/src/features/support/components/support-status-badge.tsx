"use client";

import { useTranslation } from "@/lib/i18n/use-translation";

import type { SupportStatus } from "../support-service";

const STYLE: Record<SupportStatus, string> = {
  NEW: "bg-accent-blue/10 text-accent-blue",
  IN_PROGRESS: "bg-warning/15 text-warning",
  WAITING: "bg-accent-purple/10 text-accent-purple",
  ANSWERED: "bg-success/15 text-success",
  CLOSED: "bg-surface-hover text-text-muted",
};

export default function SupportStatusBadge({ status }: { status: SupportStatus }) {
  const { t } = useTranslation();
  return (
    <span className={`inline-flex shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${STYLE[status] ?? STYLE.NEW}`} data-testid="support-status">
      {t(`support.status_${status}`)}
    </span>
  );
}
