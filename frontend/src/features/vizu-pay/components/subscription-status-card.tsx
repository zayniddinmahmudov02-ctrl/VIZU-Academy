"use client";

import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { AlertTriangle, CheckCircle2, Crown, Loader2, Lock, Ticket } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import type { PromoRedeemResult, SubscriptionStatus } from "../types";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return `${new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(new Date(value))} UTC`;
}

interface Props {
  status: SubscriptionStatus;
  onRedeemPromo: (code: string) => Promise<PromoRedeemResult>;
}

function PromoRedeemBlock({ onRedeemPromo }: { onRedeemPromo: (code: string) => Promise<PromoRedeemResult> }) {
  const { t } = useTranslation();
  const [code, setCode] = useState("");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  async function handleRedeem() {
    if (!code.trim()) return;
    setPending(true);
    setResult(null);
    try {
      const redeemed = await onRedeemPromo(code.trim());
      setResult({
        ok: true,
        message: redeemed.grantedOffers.length > 0 ? t("vizuPay.promoRedeemFreeAccessSuccess") : t("vizuPay.promoRedeemSuccess"),
      });
      setCode("");
    } catch (err: unknown) {
      const message = isAxiosError<{ message?: string }>(err) ? err.response?.data?.message : undefined;
      setResult({ ok: false, message: message ?? t("vizuPay.promoRedeemError") });
    } finally {
      setPending(false);
    }
  }

  return (
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

      {result && <p className={`mt-2 text-xs ${result.ok ? "text-success" : "text-danger"}`}>{result.message}</p>}
    </div>
  );
}

export default function SubscriptionStatusCard({ status, onRedeemPromo }: Props) {
  const { t } = useTranslation();
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="space-y-4">
      {status.isPremium && (
        <div className="rounded-card bg-gradient-to-br from-accent-blue to-purple-600 p-6 text-white shadow-[var(--shadow-md)]">
          <div className="flex items-center gap-2">
            <Crown size={20} />
            <span className="text-sm font-bold uppercase tracking-wide">{t("vizuPay.statusPremium")}</span>
          </div>
          <p className="mt-2 text-sm text-white/85">
            {t("vizuPay.statusValidUntil", { date: formatDate(status.premiumUntil) })}
          </p>
        </div>
      )}

      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        {status.isBlocked && (
          <div className="mb-4 rounded-xl bg-danger/10 p-3.5">
            <p className="flex items-center gap-1.5 text-sm font-bold text-danger">
              <Lock size={16} />
              {t("vizuPay.statusBlockedTitle")}
            </p>
            <p className="mt-2 text-sm text-text-secondary">{t("vizuPay.statusBlockedBody")}</p>
          </div>
        )}

        {!status.isPremium && (
          status.ownedLevels.length > 0 ? (
            <div className="flex flex-wrap items-center gap-2">
              <span className="flex items-center gap-1.5 text-sm font-bold text-success">
                <CheckCircle2 size={16} />
                {t("angebote.ownedTitle")}
              </span>
              {status.ownedLevels.map((level) => (
                <span key={level} className="rounded-lg bg-accent-blue/10 px-2.5 py-1 text-xs font-bold text-accent-blue">
                  {level}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-secondary">{t("angebote.noneOwned")}</p>
          )
        )}

        {status.courseAccesses.length > 0 && (
          <section className="mt-4 border-t border-surface-border pt-4">
            <h3 className="mb-3 text-sm font-bold text-text-primary">{t("angebote.accessTitle")}</h3>
            <ul className="space-y-3">
              {status.courseAccesses.map((access) => {
                const end = access.accessEndDate ? new Date(access.accessEndDate).getTime() : 0;
                const seconds = access.status === "ACTIVE"
                  ? Math.max(0, Math.floor((end - now) / 1000))
                  : 0;
                const days = Math.floor(seconds / 86_400);
                const remaining = access.status === "EXPIRED" || seconds === 0
                  ? t("angebote.accessExpired")
                  : days > 0
                    ? t("angebote.accessDays", { days })
                    : seconds >= 3_600
                      ? t("angebote.accessHours", { hours: Math.ceil(seconds / 3_600) })
                      : t("angebote.accessMinutes", { minutes: Math.ceil(seconds / 60) });
                return (
                  <li key={access.orderId} className="rounded-xl bg-surface-hover p-3.5">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-semibold text-text-primary">{access.planLabel}</p>
                      <span className={`text-xs font-bold ${access.status === "ACTIVE" ? "text-success" : "text-danger"}`}>
                        {remaining}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-text-secondary">{access.levels.join(" · ")}</p>
                    <div className="mt-2 grid gap-1 text-xs text-text-muted sm:grid-cols-2">
                      <span>{t("angebote.accessStart")}: {formatDate(access.accessStartDate)}</span>
                      <span>{t("angebote.accessEnd")}: {formatDate(access.accessEndDate)}</span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {!status.hasPendingOrder && status.latestRejectionReason && (
          <div className="mt-3 rounded-xl bg-danger/10 p-3.5">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-danger">
              <AlertTriangle size={14} />
              {t("vizuPay.statusRejectedTitle")}
            </p>
            <p className="mt-1 text-xs text-text-secondary">
              {t("vizuPay.rejectionReasonLabel")}: {status.latestRejectionReason}
            </p>
            <p className="mt-1 text-xs text-text-muted">
              {t("vizuPay.rejectionAttemptsLabel")}: {status.rejectionCount}/3
            </p>
          </div>
        )}

        <PromoRedeemBlock onRedeemPromo={onRedeemPromo} />
      </div>
    </div>
  );
}
