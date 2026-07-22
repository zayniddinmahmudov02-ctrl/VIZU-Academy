import { AlertTriangle, Crown, Sparkles } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import type { SubscriptionStatus } from "../types";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "long", year: "numeric" }).format(new Date(value));
}

interface Props {
  status: SubscriptionStatus;
  onStartTrial: () => void;
  trialPending: boolean;
}

export default function SubscriptionStatusCard({ status, onStartTrial, trialPending }: Props) {
  const { t } = useTranslation();

  if (status.isPremium) {
    const showReminder = status.isTrial && status.trialDaysRemaining !== null && status.trialDaysRemaining <= 2;

    return (
      <div className="rounded-card bg-gradient-to-br from-accent-blue to-purple-600 p-6 text-white shadow-[var(--shadow-md)]">
        <div className="flex items-center gap-2">
          <Crown size={20} />
          <span className="text-sm font-bold uppercase tracking-wide">
            {status.isTrial ? t("vizuPay.statusOnTrial") : t("vizuPay.statusPremium")}
          </span>
        </div>
        <p className="mt-2 text-sm text-white/85">
          {t("vizuPay.statusValidUntil", { date: formatDate(status.premiumUntil) })}
        </p>

        {showReminder && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-white/15 px-3 py-2 text-xs font-medium">
            <AlertTriangle size={14} />
            {t("vizuPay.statusTrialReminder", { days: String(status.trialDaysRemaining) })}
          </div>
        )}
      </div>
    );
  }

  if (status.trialAvailable) {
    return (
      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <div className="flex items-center gap-2 text-accent-blue">
          <Sparkles size={20} />
          <span className="text-sm font-bold uppercase tracking-wide">{t("vizuPay.statusTrialTitle")}</span>
        </div>
        <p className="mt-2 text-sm text-text-secondary">{t("vizuPay.statusTrialBody")}</p>
        <button
          type="button"
          onClick={onStartTrial}
          disabled={trialPending}
          className="mt-4 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {t("vizuPay.statusStartTrial")}
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <p className="text-sm text-text-secondary">{t("vizuPay.statusNoPremium")}</p>
    </div>
  );
}
