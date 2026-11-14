"use client";

import { Dialog } from "@base-ui/react/dialog";
import { AlertTriangle } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import type { Offer } from "../types";

/** Shown before the checkout of a package that contains levels not released yet (A1–C1: B2 / C1). The payment
 * starts only after "Verstanden"; "Abbrechen" closes it. */
export default function PackageWarningModal({ offer, onConfirm, onCancel }: { offer: Offer | null; onConfirm: () => void; onCancel: () => void }) {
  const { t } = useTranslation();
  return (
    <Dialog.Root open={offer !== null} onOpenChange={(open) => !open && onCancel()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm" />
        <Dialog.Popup
          data-testid="package-warning"
          className="fixed left-1/2 top-1/2 z-[61] max-h-[90vh] w-[92vw] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-card bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border outline-none"
        >
          <Dialog.Title className="flex items-start gap-2.5 text-lg font-bold text-text-primary">
            <AlertTriangle size={22} className="mt-0.5 shrink-0 text-warning" />
            {t("angebote.a1c1WarningTitle")}
          </Dialog.Title>
          <Dialog.Description className="mt-3 text-sm leading-relaxed text-text-secondary">{t("angebote.a1c1WarningBody")}</Dialog.Description>
          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onCancel}
              data-testid="package-warning-cancel"
              className="rounded-xl px-4 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border transition-colors hover:bg-surface-hover"
            >
              {t("angebote.cancel")}
            </button>
            <button
              type="button"
              onClick={onConfirm}
              data-testid="package-warning-confirm"
              className="rounded-xl bg-orange-500 px-4 py-2.5 text-sm font-bold text-white shadow-md transition-colors hover:bg-orange-600"
            >
              {t("angebote.a1c1Confirm")}
            </button>
          </div>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
