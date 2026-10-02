"use client";

import { useState } from "react";
import { Tag } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { useVizuPay } from "../hooks/use-vizu-pay";
import OfferCard from "../components/offer-card";
import SubscriptionStatusCard from "../components/subscription-status-card";
import OrderHistoryList from "../components/order-history-list";
import CheckoutModal from "../components/checkout-modal";
import { offerState } from "../offer-state";
import type { Offer, PlanOption } from "../types";

/** "Angebote" (formerly VIZU-Pay): the two packages (A1 → B1, A1 → C1),
 * the single levels, purchase status and payment history. Every price
 * comes from GET /vizu-pay/offers. `?offer=A1` (from a course card) opens
 * the checkout for that offer directly. */
export default function VizuPayPage() {
  const { t } = useTranslation();
  const { offers, paymentCards, status, orders, loading, error, redeemPromo, submitOrder } = useVizuPay();

  const [picked, setPicked] = useState<Offer | null>(null);
  // `?offer=A1` from a course card — read once, cleared when the modal closes.
  const [requestedCode, setRequestedCode] = useState<string | null>(() =>
    typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("offer"),
  );

  const packages = offers.filter((o) => o.kind === "PACKAGE");
  const levels = offers.filter((o) => o.kind === "LEVEL");

  const requested = offers.find((o) => o.code === requestedCode);
  const selected = picked ?? (requested && offerState(requested, status) === "available" ? requested : null);

  function closeCheckout() {
    setPicked(null);
    setRequestedCode(null);
  }

  const checkoutPlan: PlanOption | null = selected
    ? { plan: selected.code, label: selected.label, days: 0, price: selected.salePrice ?? 0, currency: selected.currency }
    : null;

  async function handleCheckoutSubmit(paymentMethod: string, promoCode: string | undefined, proofFile: File) {
    await submitOrder({ plan: selected!.code, paymentMethod, promoCode, proofFile });
  }

  return (
    <div className="space-y-8">
      <PageHeader icon={Tag} titleKey="angebote.title" subtitleKey="angebote.subtitle" gradient="from-accent-blue to-orange-500" />

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
        <div className="mx-auto max-w-5xl space-y-10">
          <SubscriptionStatusCard status={status} onRedeemPromo={redeemPromo} />

          {status.hasPendingOrder && !status.isBlocked && (
            <div className="rounded-card bg-warning/10 p-4 text-center text-sm font-medium text-warning ring-1 ring-warning/20">
              {t("vizuPay.pendingNotice")}
            </div>
          )}

          <section>
            <h2 className="mb-1 text-lg font-bold text-text-primary">{t("angebote.packagesTitle")}</h2>
            <p className="mb-5 text-sm text-text-secondary">{t("angebote.packagesSubtitle")}</p>
            <div className="grid gap-6 md:grid-cols-2">
              {packages.map((offer) => (
                <OfferCard
                  key={offer.code}
                  offer={offer}
                  state={offerState(offer, status)}
                  highlighted={offer.levels.length === Math.max(...packages.map((p) => p.levels.length))}
                  onBuy={() => setPicked(offer)}
                />
              ))}
            </div>
          </section>

          <section>
            <h2 className="mb-1 text-lg font-bold text-text-primary">{t("angebote.levelsTitle")}</h2>
            <p className="mb-5 text-sm text-text-secondary">{t("angebote.levelsSubtitle")}</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {levels.map((offer) => (
                <OfferCard key={offer.code} offer={offer} state={offerState(offer, status)} compact onBuy={() => setPicked(offer)} />
              ))}
            </div>
          </section>

          <section>
            <h2 className="mb-4 text-lg font-bold text-text-primary">{t("vizuPay.historyTitle")}</h2>
            <OrderHistoryList orders={orders?.items ?? []} />
          </section>
        </div>
      )}

      <CheckoutModal
        plan={checkoutPlan}
        paymentCards={paymentCards}
        onClose={closeCheckout}
        onSubmit={handleCheckoutSubmit}
      />
    </div>
  );
}
