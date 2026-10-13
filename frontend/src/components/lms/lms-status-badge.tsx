"use client";

import { CheckCircle2, Circle, CircleDashed, Clock3, Lock } from "lucide-react";

import type { CompetencyStatus } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export const STATUS_META: Record<CompetencyStatus, { labelKey: string; tone: string; icon: typeof Circle }> = {
  not_started: { labelKey: "lms.statusNotStarted", tone: "bg-surface-hover text-text-secondary ring-surface-border", icon: Circle },
  in_progress: { labelKey: "lms.statusInProgress", tone: "bg-accent-blue/10 text-accent-blue ring-accent-blue/20", icon: Clock3 },
  completed: { labelKey: "lms.statusCompleted", tone: "bg-success/10 text-success ring-success/20", icon: CheckCircle2 },
  locked: { labelKey: "lms.statusLocked", tone: "bg-warning/10 text-warning ring-warning/20", icon: Lock },
  not_available: { labelKey: "lms.statusNotAvailable", tone: "bg-surface-hover text-text-muted ring-surface-border", icon: CircleDashed },
};

/** Status chip — the status always comes from the backend. `detail`
 * ("pending_evaluation") refines "In Bearbeitung" while a submission waits
 * for grading. */
export default function LmsStatusBadge({ status, detail, className }: { status: CompetencyStatus; detail?: string | null; className?: string }) {
  const { t } = useTranslation();
  const meta = STATUS_META[status];
  const Icon = meta.icon;
  const label = status === "in_progress" && detail === "pending_evaluation" ? t("lms.statusPendingEvaluation") : t(meta.labelKey);

  return (
    <span
      className={cn("inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1", meta.tone, className)}
      data-status={status}
    >
      <Icon size={13} aria-hidden="true" />
      {label}
    </span>
  );
}
