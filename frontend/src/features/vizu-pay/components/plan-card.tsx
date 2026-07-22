import { Check } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import type { PlanOption } from "../types";

interface Props {
  plan: PlanOption;
  highlighted?: boolean;
  onSelect: () => void;
}

export default function PlanCard({ plan, highlighted, onSelect }: Props) {
  const { t } = useTranslation();
  const perMonth = Math.round(plan.price / (plan.days / 30));

  return (
    <div
      className={`relative flex flex-col rounded-card p-6 shadow-[var(--shadow-md)] ring-1 ${
        highlighted ? "bg-gradient-to-br from-accent-blue to-purple-600 text-white ring-transparent" : "bg-surface-card text-text-primary ring-surface-border"
      }`}
    >
      {highlighted && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-white px-3 py-1 text-[11px] font-bold text-accent-blue shadow">
          {t("vizuPay.plansPopular")}
        </span>
      )}

      <h3 className={`text-lg font-bold ${highlighted ? "text-white" : "text-text-primary"}`}>{plan.label}</h3>

      <div className="mt-3">
        <span className="text-3xl font-extrabold">{new Intl.NumberFormat("de-DE").format(plan.price)}</span>
        <span className={`ml-1 text-sm ${highlighted ? "text-white/80" : "text-text-muted"}`}>UZS</span>
      </div>
      <p className={`mt-1 text-xs ${highlighted ? "text-white/70" : "text-text-muted"}`}>
        ≈ {new Intl.NumberFormat("de-DE").format(perMonth)} UZS / {t("vizuPay.plansPerMonth")}
      </p>

      <ul className="mt-5 flex-1 space-y-2 text-sm">
        {[t("vizuPay.plansFeatureFull"), t("vizuPay.plansFeatureCertificates"), t("vizuPay.plansFeatureSupport")].map((f) => (
          <li key={f} className={`flex items-center gap-2 ${highlighted ? "text-white/90" : "text-text-secondary"}`}>
            <Check size={14} className={highlighted ? "text-white" : "text-success"} />
            {f}
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={onSelect}
        className={`mt-6 w-full rounded-xl py-2.5 text-sm font-semibold transition-opacity hover:opacity-90 ${
          highlighted ? "bg-white text-accent-blue" : "bg-accent-blue text-white"
        }`}
      >
        {t("vizuPay.plansSelect")}
      </button>
    </div>
  );
}
