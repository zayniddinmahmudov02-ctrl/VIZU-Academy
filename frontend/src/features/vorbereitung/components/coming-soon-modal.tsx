"use client";

import { Dialog } from "@base-ui/react/dialog";
import { Lock, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  open: boolean;
  onClose: () => void;
}

/** Same @base-ui/react/dialog primitive as every other VIZU modal (see
 * features/vizu-pay/components/checkout-modal.tsx) — not a new dialog
 * system, just a small, reusable "this isn't ready yet" instance of it.
 * Used by the static, fully-locked Multilevel section below (no task
 * content exists for it yet — see vorbereitung-view.tsx) — nothing here
 * fetches data or navigates anywhere. */
export default function ComingSoonModal({ open, onClose }: Props) {
  const { t } = useTranslation();

  return (
    <Dialog.Root open={open} onOpenChange={(next) => !next && onClose()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm" />
        <Dialog.Popup className="fixed left-1/2 top-1/2 z-[61] w-[92vw] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-card bg-surface-card p-6 text-center shadow-[var(--shadow-lg)] ring-1 ring-surface-border outline-none">
          <Dialog.Close className="absolute right-4 top-4 rounded-lg p-1 text-text-muted transition-colors hover:bg-surface-hover hover:text-text-primary">
            <X size={18} />
          </Dialog.Close>

          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-warning/10 text-warning">
            <Lock size={26} />
          </div>

          <h3 className="mt-4 text-lg font-bold text-text-primary">{t("vorbereitung.comingSoonTitle")}</h3>
          <p className="mt-2 text-sm leading-relaxed text-text-secondary">
            {t("vorbereitung.comingSoonBody")}
          </p>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
