"use client";

import { useState } from "react";
import { CreditCard } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { useVizuPay } from "../hooks/use-vizu-pay";
import PlanCard from "../components/plan-card";
import SubscriptionStatusCard from "../components/subscription-status-card";
import OrderHistoryList from "../components/order-history-list";
import CheckoutModal from "../components/checkout-modal";
import type { PlanOption } from "../types";

export default function VizuPayPage() {
  const { t } = useTranslation();
  const { plans, status, orders, loading, error, activateTrial, submitOrder } = useVizuPay();

  const [selectedPlan, setSelectedPlan] = useState<PlanOption | null>(null);
  const [trialPending, setTrialPending] = useState(false);

  async function handleStartTrial() {
    setTrialPending(true);
    try {
      await activateTrial();
    } finally {
      setTrialPending(false);
    }
  }

  async function handleCheckoutSubmit(paymentMethod: string, promoCode: string | undefined, proofFile: File) {
    await submitOrder({ plan: selectedPlan!.plan, paymentMethod, promoCode, proofFile });
  }

  return (
    <div className="space-y-8">
      <PageHeader icon={CreditCard} titleKey="vizuPay.title" subtitleKey="vizuPay.subtitle" gradient="from-accent-blue to-purple-600" />

      {loading && (
        <div className="flex justify-center py-16">
          <div className="h-10 w-10 animate-spin rounded-full border-[3px] border-surface-border border-t-accent-blue" />
        </div>
      )}

      {error && !loading && (
        <div className="rounded-card bg-surface-card p-8 text-center text-sm text-text-secondary shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          {t("vizuPay.error")}
        </div>
      )}

      {!loading && !error && status && (
        <div className="mx-auto max-w-5xl space-y-8">
          <SubscriptionStatusCard status={status} onStartTrial={handleStartTrial} trialPending={trialPending} />

          {status.hasPendingOrder && (
            <div className="rounded-card bg-warning/10 p-4 text-center text-sm font-medium text-warning ring-1 ring-warning/20">
              {t("vizuPay.pendingNotice")}
            </div>
          )}

          <div>
            <h2 className="mb-4 text-lg font-bold text-text-primary">{t("vizuPay.plansTitle")}</h2>
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
              {plans.map((plan, index) => (
                <PlanCard key={plan.plan} plan={plan} highlighted={index === 1} onSelect={() => setSelectedPlan(plan)} />
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-4 text-lg font-bold text-text-primary">{t("vizuPay.historyTitle")}</h2>
            <OrderHistoryList orders={orders?.items ?? []} />
          </div>
        </div>
      )}

      <CheckoutModal plan={selectedPlan} onClose={() => setSelectedPlan(null)} onSubmit={handleCheckoutSubmit} />
    </div>
  );
}
