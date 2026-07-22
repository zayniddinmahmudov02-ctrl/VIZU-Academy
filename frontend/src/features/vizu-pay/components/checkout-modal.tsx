"use client";

import { useState } from "react";
import { Dialog } from "@base-ui/react/dialog";
import { Loader2, UploadCloud, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { validatePromo } from "../services/vizu-pay-service";
import { PAYMENT_METHODS } from "../types";
import type { PlanOption } from "../types";

interface Props {
  plan: PlanOption | null;
  onClose: () => void;
  onSubmit: (paymentMethod: string, promoCode: string | undefined, proofFile: File) => Promise<void>;
}

export default function CheckoutModal({ plan, onClose, onSubmit }: Props) {
  const { t } = useTranslation();

  const [paymentMethod, setPaymentMethod] = useState<string>(PAYMENT_METHODS[0]);
  const [promoCode, setPromoCode] = useState("");
  const [promoResult, setPromoResult] = useState<{ valid: boolean; message: string | null; discountType: string | null; discountValue: number | null } | null>(null);
  const [checkingPromo, setCheckingPromo] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!plan) return null;

  const discount = promoResult?.valid
    ? promoResult.discountType === "PERCENT"
      ? Math.round((plan.price * (promoResult.discountValue ?? 0)) / 100)
      : Math.min(promoResult.discountValue ?? 0, plan.price)
    : 0;
  const finalPrice = Math.max(plan.price - discount, 0);

  async function handleCheckPromo() {
    if (!promoCode.trim()) return;
    setCheckingPromo(true);
    try {
      const result = await validatePromo(promoCode.trim());
      setPromoResult(result);
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
      await onSubmit(paymentMethod, promoResult?.valid ? promoCode.trim() : undefined, file);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.message ?? t("vizuPay.checkoutSubmitError"));
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
                  value={promoCode}
                  onChange={(e) => {
                    setPromoCode(e.target.value.toUpperCase());
                    setPromoResult(null);
                  }}
                  placeholder={t("vizuPay.checkoutPromoPlaceholder")}
                  className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60"
                />
                <button
                  type="button"
                  onClick={handleCheckPromo}
                  disabled={!promoCode.trim() || checkingPromo}
                  className="shrink-0 rounded-xl border border-surface-border px-3 text-xs font-semibold text-text-secondary transition-colors hover:bg-surface-hover disabled:opacity-40"
                >
                  {checkingPromo ? <Loader2 size={14} className="animate-spin" /> : t("vizuPay.checkoutApply")}
                </button>
              </div>
              {promoResult && (
                <p className={`mt-1.5 text-xs ${promoResult.valid ? "text-success" : "text-danger"}`}>
                  {promoResult.valid ? t("vizuPay.checkoutPromoApplied") : promoResult.message}
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
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
              </label>
            </div>

            <div className="rounded-xl bg-surface-hover p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary">{t("vizuPay.checkoutSubtotal")}</span>
                <span className={discount > 0 ? "text-text-muted line-through" : "text-text-primary"}>
                  {new Intl.NumberFormat("de-DE").format(plan.price)} UZS
                </span>
              </div>
              {discount > 0 && (
                <div className="mt-1 flex items-center justify-between text-sm text-success">
                  <span>{t("vizuPay.checkoutDiscount")}</span>
                  <span>-{new Intl.NumberFormat("de-DE").format(discount)} UZS</span>
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
              disabled={submitting}
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
