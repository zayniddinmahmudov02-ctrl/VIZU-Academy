"use client";

import { useState } from "react";
import { Crown, Loader2, Ticket } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import type { PromoRedeemResult, SubscriptionStatus } from "../types";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "long", year: "numeric" }).format(new Date(value));
}

interface Props {
  status: SubscriptionStatus;
  onRedeemPromo: (code: string) => Promise<PromoRedeemResult>;
}

export default function SubscriptionStatusCard({ status, onRedeemPromo }: Props) {
  const { t } = useTranslation();
  const [code, setCode] = useState("");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  async function handleRedeem() {
    if (!code.trim()) return;
    setPending(true);
    setResult(null);
    try {
      await onRedeemPromo(code.trim());
      setResult({ ok: true, message: t("vizuPay.promoRedeemSuccess") });
      setCode("");
    } catch (err: any) {
      setResult({ ok: false, message: err?.response?.data?.message ?? t("vizuPay.promoRedeemError") });
    } finally {
      setPending(false);
    }
  }

  if (status.isPremium) {
    return (
      <div className="rounded-card bg-gradient-to-br from-accent-blue to-purple-600 p-6 text-white shadow-[var(--shadow-md)]">
        <div className="flex items-center gap-2">
          <Crown size={20} />
          <span className="text-sm font-bold uppercase tracking-wide">{t("vizuPay.statusPremium")}</span>
        </div>
        <p className="mt-2 text-sm text-white/85">
          {t("vizuPay.statusValidUntil", { date: formatDate(status.premiumUntil) })}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <p className="text-sm text-text-secondary">{t("vizuPay.statusNoPremium")}</p>

      <div className="mt-4 border-t border-surface-border pt-4">
        <div className="flex items-center gap-2 text-accent-blue">
          <Ticket size={18} />
          <span className="text-sm font-bold">{t("vizuPay.promoRedeemTitle")}</span>
        </div>

        <div className="mt-2.5 flex gap-2">
          <input
            value={code}
            onChange={(e) => {
              setCode(e.target.value.toUpperCase());
              setResult(null);
            }}
            placeholder={t("vizuPay.promoRedeemPlaceholder")}
            className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60"
          />
          <button
            type="button"
            onClick={handleRedeem}
            disabled={!code.trim() || pending}
            className="flex shrink-0 items-center gap-1.5 rounded-xl bg-accent-blue px-4 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {pending && <Loader2 size={14} className="animate-spin" />}
            {t("vizuPay.promoRedeemButton")}
          </button>
        </div>

        {result && (
          <p className={`mt-2 text-xs ${result.ok ? "text-success" : "text-danger"}`}>{result.message}</p>
        )}
      </div>
    </div>
  );
}
