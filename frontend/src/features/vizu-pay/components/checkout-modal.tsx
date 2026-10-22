"use client";

import { useState } from "react";
import { isAxiosError } from "axios";
import { useQuery } from "@tanstack/react-query";
import { Dialog } from "@base-ui/react/dialog";
import { Check, Copy, Loader2, UploadCloud, X } from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { updateProfile } from "@/features/profile/services/profile-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { getCheckoutQuote, validatePromo } from "../services/vizu-pay-service";
import { PAYMENT_METHODS } from "../types";
import type { PaymentCard, PlanOption } from "../types";

interface Props {
  plan: PlanOption | null;
  paymentCards: PaymentCard[];
  onClose: () => void;
  onSubmit: (paymentMethod: string, promoCode: string | undefined, proofFile: File) => Promise<void>;
}

// Mirrors the backend's MAX_PROOF_SIZE_BYTES (vizu_pay/service.py) — checked
// client-side too so a too-large file never even starts uploading.
const MAX_PROOF_SIZE_BYTES = 10 * 1024 * 1024;

function CardRow({ card }: { card: PaymentCard }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(card.number);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex items-center justify-between gap-2 rounded-xl bg-surface-hover px-3.5 py-2.5">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">{card.label}</p>
        {/* shown in groups of four, copied as plain digits */}
        <p className="font-mono text-sm font-semibold text-text-primary">{card.number.replace(/\s/g, "").replace(/(\d{4})(?=\d)/g, "$1 ")}</p>
      </div>
      <button
        type="button"
        onClick={handleCopy}
        className="flex shrink-0 items-center gap-1.5 rounded-lg border border-surface-border px-3 py-1.5 text-xs font-semibold text-text-secondary transition-colors hover:bg-surface-card"
      >
        {copied ? <Check size={13} className="text-success" /> : <Copy size={13} />}
        {copied ? t("vizuPay.paymentCardCopied") : t("vizuPay.paymentCardCopy")}
      </button>
    </div>
  );
}

type CheckoutUser = ReturnType<typeof useCurrentUser>["user"];

export default function CheckoutModal(props: Props) {
  const { user } = useCurrentUser();
  const profileKey = [user?.id, user?.firstName, user?.lastName, user?.phoneNumber].join(":");
  return <CheckoutModalContent key={`${props.plan?.plan ?? "closed"}:${profileKey}`} {...props} user={user} />;
}

function CheckoutModalContent({ plan, paymentCards, onClose, onSubmit, user }: Props & { user: CheckoutUser }) {
  const { t, language } = useTranslation();

  const [paymentMethod, setPaymentMethod] = useState<string>(PAYMENT_METHODS[0]);
  const [promoCode, setPromoCode] = useState("");
  const [promoResult, setPromoResult] = useState<{
    valid: boolean;
    message: string | null;
    discountType: string | null;
    discountValue: number | null;
    plan: string;
  } | null>(null);
  const [checkingPromo, setCheckingPromo] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [firstName, setFirstName] = useState(user?.firstName ?? "");
  const [lastName, setLastName] = useState(user?.lastName ?? "");
  const [phoneNumber, setPhoneNumber] = useState(user?.phoneNumber ?? "");

  // the price is the server's (sale price, promo, medal reward) — the order recomputes it again
  const promoIsForSelectedPlan = promoResult?.plan === plan?.plan;
  const appliedPromo = promoResult?.valid && promoIsForSelectedPlan ? promoCode.trim() : "";
  const { data: quote, isFetching: quoteLoading, isError: quoteError } = useQuery({
    queryKey: ["vizu-pay", "quote", plan?.plan, appliedPromo],
    queryFn: () => getCheckoutQuote(plan!.plan, appliedPromo || undefined),
    enabled: !!plan,
    staleTime: 0,
  });

  if (!plan) return null;

  const subtotal = quote?.base_amount ?? plan.price;
  const discount = quote?.promo_discount ?? 0;
  const rewardDiscount = quote?.reward_discount ?? 0;
  const rewardName = quote?.reward_name ? (language === "uz" ? quote.reward_name.uz : quote.reward_name.de) : "";
  const finalPrice = quote?.final_amount ?? plan.price;

  async function handleCheckPromo() {
    if (!promoCode.trim()) return;
    setCheckingPromo(true);
    try {
      const result = await validatePromo(promoCode.trim(), plan!.plan);
      setPromoResult({ ...result, plan: plan!.plan });
    } catch {
      setPromoResult({
        valid: false,
        message: t("vizuPay.checkoutSubmitError"),
        discountType: null,
        discountValue: null,
        plan: plan!.plan,
      });
    } finally {
      setCheckingPromo(false);
    }
  }

  async function handleSubmit() {
    if (!file) {
      setError(t("vizuPay.checkoutProofRequired"));
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const changed =
        user &&
        (firstName !== (user.firstName ?? "") ||
          lastName !== (user.lastName ?? "") ||
          phoneNumber !== (user.phoneNumber ?? ""));
      if (changed) {
        await updateProfile({ firstName, lastName, phoneNumber });
      }
      await onSubmit(
        paymentMethod,
        promoResult?.valid && promoIsForSelectedPlan ? promoCode.trim() : undefined,
        file,
      );
      onClose();
    } catch (err: unknown) {
      const code = isAxiosError<{ message?: string; detail?: string }>(err)
        ? err.response?.data?.message ?? err.response?.data?.detail
        : undefined;
      if (code === "PAYMENT_REQUEST_BLOCKED") {
        setError(t("vizuPay.checkoutBlockedError"));
      } else if (code === "PAYMENT_REQUEST_ALREADY_PENDING") {
        setError(t("vizuPay.checkoutPendingError"));
      } else {
        setError(code ?? t("vizuPay.checkoutSubmitError"));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog.Root open={plan !== null} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm" />
        <Dialog.Popup className="fixed left-1/2 top-1/2 z-[61] max-h-[90vh] w-[92vw] max-w-md -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-card bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border outline-none">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-bold text-text-primary">{plan.label}</h3>
            <Dialog.Close className="rounded-lg p-1 text-text-muted transition-colors hover:bg-surface-hover hover:text-text-primary">
              <X size={18} />
            </Dialog.Close>
          </div>

          <div className="space-y-4">
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
                {t("vizuPay.paymentCardsTitle")}
              </p>
              <div className="space-y-2">
                {paymentCards.map((card) => (
                  <CardRow key={card.number} card={card} />
                ))}
              </div>
              <p className="mt-2 text-xs text-text-secondary">{t("vizuPay.paymentInstructions")}</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("vizuPay.checkoutFirstName")}</label>
                <input
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("vizuPay.checkoutLastName")}</label>
                <input
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60"
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("vizuPay.checkoutPhone")}</label>
              <input
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+998 90 123 45 67"
                className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("vizuPay.checkoutPaymentMethod")}</label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60"
              >
                {PAYMENT_METHODS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("vizuPay.checkoutPromoCode")}</label>
              <div className="flex gap-2">
                <input
                  aria-label={t("vizuPay.checkoutPromoCode")}
                  value={promoCode}
                  onChange={(e) => {
                    setPromoCode(e.target.value.toUpperCase());
                    setPromoResult(null);
                  }}
                  placeholder={t("vizuPay.checkoutPromoPlaceholder")}
                  className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60"
                />
                {promoResult?.valid && promoIsForSelectedPlan && (
                  <button
                    type="button"
                    onClick={() => { setPromoCode(""); setPromoResult(null); }}
                    className="shrink-0 rounded-xl border border-surface-border px-3 text-xs font-semibold text-text-secondary transition-colors hover:bg-surface-hover"
                    aria-label={language === "uz" ? "Promokodni olib tashlash" : "Gutscheincode entfernen"}
                  >
                    <X size={14} />
                  </button>
                )}
                <button
                  type="button"
                  onClick={handleCheckPromo}
                  disabled={!promoCode.trim() || checkingPromo || quoteLoading}
                  className="shrink-0 rounded-xl border border-surface-border px-3 text-xs font-semibold text-text-secondary transition-colors hover:bg-surface-hover disabled:opacity-40"
                >
                  {checkingPromo || quoteLoading ? <Loader2 size={14} className="animate-spin" /> : t("vizuPay.checkoutApply")}
                </button>
              </div>
              {quoteLoading && <p className="mt-1.5 text-xs text-text-muted" role="status">{language === "uz" ? "Narx tekshirilmoqda…" : "Preis wird geprüft…"}</p>}
              {quoteError && <p className="mt-1.5 text-xs text-danger" role="alert">{language === "uz" ? "Server narxini olish amalga oshmadi. Qayta urinib ko‘ring." : "Serverpreis konnte nicht geladen werden. Bitte erneut versuchen."}</p>}
              {promoResult && promoIsForSelectedPlan && (
                <p className={`mt-1.5 text-xs ${promoResult.valid ? "text-success" : "text-danger"}`}>
                  {promoResult.valid && !quote?.promo_error
                    ? t("vizuPay.checkoutPromoApplied")
                    : quote?.promo_error ?? promoResult.message}
                </p>
              )}
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("vizuPay.checkoutProof")}</label>
              <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-surface-border bg-surface-hover p-4 text-sm text-text-secondary transition-colors hover:border-accent-blue/50">
                <UploadCloud size={18} />
                {file ? file.name : t("vizuPay.checkoutProofUpload")}
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png,.webp,.pdf"
                  className="hidden"
                  onChange={(e) => {
                    const selected = e.target.files?.[0] ?? null;
                    if (selected && selected.size > MAX_PROOF_SIZE_BYTES) {
                      setError(t("vizuPay.checkoutProofTooLarge"));
                      setFile(null);
                      e.target.value = "";
                      return;
                    }
                    setError(null);
                    setFile(selected);
                  }}
                />
              </label>
              <p className="mt-1 text-[11px] text-text-muted">{t("vizuPay.checkoutProofHint")}</p>
            </div>

            <div className="rounded-xl bg-surface-hover p-4">
              {quote?.original_price != null && quote.original_price > subtotal && (
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="text-text-secondary">{t("vizuPay.checkoutOriginalPrice")}</span>
                  <span className="text-text-muted line-through">
                    {new Intl.NumberFormat("de-DE").format(quote.original_price)} UZS
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary">{t("vizuPay.checkoutSubtotal")}</span>
                <span className={discount + rewardDiscount > 0 ? "text-text-muted line-through" : "text-text-primary"}>
                  {new Intl.NumberFormat("de-DE").format(subtotal)} UZS
                </span>
              </div>
              {discount > 0 && (
                <div className="mt-1 flex items-center justify-between text-sm text-success">
                  <span>{t("vizuPay.checkoutDiscount")}</span>
                  <span>-{new Intl.NumberFormat("de-DE").format(discount)} UZS</span>
                </div>
              )}
              {rewardDiscount > 0 && (
                <div className="mt-1 flex items-center justify-between text-sm text-success" data-testid="checkout-reward">
                  <span>{t("vizuPay.checkoutRewardDiscount", { name: rewardName })}</span>
                  <span>-{new Intl.NumberFormat("de-DE").format(rewardDiscount)} UZS</span>
                </div>
              )}
              <div className="mt-2 flex items-center justify-between border-t border-surface-border pt-2 text-base font-bold text-text-primary">
                <span>{t("vizuPay.checkoutTotal")}</span>
                <span>{new Intl.NumberFormat("de-DE").format(finalPrice)} UZS</span>
              </div>
            </div>

            {error && <p className="text-xs text-danger">{error}</p>}

            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting || quoteLoading || quoteError || !quote}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent-blue py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {submitting ? <Loader2 size={16} className="animate-spin" /> : null}
              {t("vizuPay.checkoutSubmit")}
            </button>
          </div>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
