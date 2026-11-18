"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Tag } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { useVizuPay } from "../hooks/use-vizu-pay";
import OfferCard, { laterLevels } from "../components/offer-card";
import PackageWarningModal from "../components/package-warning-modal";
import { getMyPromoRequests } from "../services/vizu-pay-service";
import SubscriptionStatusCard from "../components/subscription-status-card";
import OrderHistoryList from "../components/order-history-list";
import CheckoutModal from "../components/checkout-modal";
import CoursePromoRequest from "../components/course-promo-request";
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
  // a package with levels not released yet (A1–C1): the warning comes first, the checkout only after "Verstanden"
  const [warnFor, setWarnFor] = useState<Offer | null>(null);
  const { data: promoRequests = [] } = useQuery({ queryKey: ["vizu-pay", "promo-requests"], queryFn: getMyPromoRequests });

  function buy(offer: Offer) {
    if (offer.kind === "PACKAGE" && laterLevels(offer).length > 0) setWarnFor(offer);
    else setPicked(offer);
  }
  // `?offer=A1` from a course card — read once, cleared when the modal closes.
  const [requestedCode, setRequestedCode] = useState<string | null>(() =>
    typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("offer"),
  );

  const packages = offers.filter((o) => o.kind === "PACKAGE");
  const levels = offers.filter((o) => o.kind === "LEVEL");

  const requested = offers.find((o) => o.code === requestedCode);
  const requestedOk = requested && offerState(requested, status) === "available" && laterLevels(requested).length === 0;
  const selected = picked ?? (requestedOk ? requested : null);

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
                  highlighted={offer.status === "ACTIVE" && offer.levels.length === Math.max(...packages.filter((p) => p.status === "ACTIVE").map((p) => p.levels.length))}
                  onBuy={() => buy(offer)}
                />
              ))}
            </div>
          </section>

          <section>
            <h2 className="mb-1 text-lg font-bold text-text-primary">{t("angebote.levelsTitle")}</h2>
            <p className="mb-5 text-sm text-text-secondary">{t("angebote.levelsSubtitle")}</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {levels.map((offer) => (
                <OfferCard key={offer.code} offer={offer} state={offerState(offer, status)} compact onBuy={() => buy(offer)} />
              ))}
            </div>
          </section>

          <CoursePromoRequest offers={offers} ownedLevels={status.ownedLevels} />

          {promoRequests.length > 0 && (
            <section data-testid="promo-requests">
              <h2 className="mb-3 text-lg font-bold text-text-primary">{t("angebote.promoRequestsTitle")}</h2>
              <ul className="space-y-2">
                {promoRequests.map((r) => (
                  <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-surface-card px-4 py-3 text-sm ring-1 ring-surface-border"
                    data-testid="promo-request-row" data-kind={r.kind} data-status={r.status}>
                    <span className="font-semibold text-text-primary">
                      {r.kind === "COURSE_REQUEST" ? t("angebote.courseRequestKind") : r.code} · {r.planLabel}
                    </span>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                      r.status === "APPROVED" ? "bg-success/15 text-success" : r.status === "PENDING_APPROVAL" ? "bg-warning/15 text-warning"
                        : r.status === "REJECTED" ? "bg-danger/15 text-danger" : "bg-surface-hover text-text-muted"}`}>
                      {t(`angebote.requestStatus${r.status}`)}
                    </span>
                    {r.kind === "COURSE_REQUEST" && r.code && (
                      <div className="w-full rounded-lg bg-success/10 px-3 py-2 text-xs text-text-primary" data-testid="promo-request-code">
                        <p className="font-mono text-sm font-bold">{t("angebote.courseRequestYourCode", { code: r.code })}</p>
                        {r.discount && (
                          <p className="text-text-secondary">
                            {r.discount.type === "PERCENT" ? t("angebote.courseRequestPercent", { value: r.discount.value })
                              : r.discount.type === "FIXED" ? t("angebote.courseRequestFixed", { value: r.discount.value })
                                : t("angebote.courseRequestFree")} · {t("angebote.courseRequestUse")}
                          </p>
                        )}
                      </div>
                    )}
                    {r.reason && <p className="w-full text-xs text-text-muted">{r.reason}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h2 className="mb-4 text-lg font-bold text-text-primary">{t("vizuPay.historyTitle")}</h2>
            <OrderHistoryList orders={orders?.items ?? []} />
          </section>
        </div>
      )}

      <PackageWarningModal
        offer={warnFor}
        onCancel={() => setWarnFor(null)}
        onConfirm={() => {
          setPicked(warnFor);
          setWarnFor(null);
        }}
      />

      <CheckoutModal
        plan={checkoutPlan}
        paymentCards={paymentCards}
        onClose={closeCheckout}
        onSubmit={handleCheckoutSubmit}
      />
    </div>
  );
}
