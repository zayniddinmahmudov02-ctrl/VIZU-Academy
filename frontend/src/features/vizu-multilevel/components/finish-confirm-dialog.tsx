"use client";

import { AlertTriangle } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  isSubmitting?: boolean;
  /** When set, finishing is not allowed yet (e.g. fewer than 5 answers):
   * the reason is shown and the confirm button is disabled. */
  blockedReason?: string | null;
  /** Optional overrides of the default title / body / confirm label. */
  title?: string;
  body?: string;
  confirmLabel?: string;
}

/** Shared confirmation modal for VIZU-Multilevel's persistent "Yakunlash"
 * button (see step-shell.tsx) — used identically by Lesen, Hören,
 * Schreiben and Sprechen instead of each step re-implementing its own
 * overlay/card markup. Confirming always triggers that step's own
 * existing submit path (server-side grading already treats an
 * unanswered question as incorrect/0 points — see lesen_service.py /
 * hoeren_service.py — so ending early needs no new backend logic). */
export default function VizuMultilevelFinishConfirmDialog({
  open,
  onCancel,
  onConfirm,
  isSubmitting,
  blockedReason,
  title,
  body,
  confirmLabel,
}: Props) {
  const { t } = useTranslation();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-sm space-y-4 rounded-2xl bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border">
        <div className="flex items-start gap-3">
          <AlertTriangle size={20} className="mt-0.5 shrink-0 text-warning" />
          <div>
            <p className="text-sm font-bold text-text-primary">{title ?? t("vizuMultilevel.finishConfirmTitle")}</p>
            <p className="mt-1 text-sm text-text-secondary">{body ?? t("vizuMultilevel.finishConfirmBody")}</p>
            {blockedReason && <p className="mt-2 text-sm font-semibold text-orange-600">{blockedReason}</p>}
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            {t("vizuMultilevel.schreibenConfirmCancel")}
          </Button>
          <Button onClick={onConfirm} disabled={isSubmitting || !!blockedReason}>
            {isSubmitting ? t("common.loading") : (confirmLabel ?? t("vizuMultilevel.finishConfirmSubmit"))}
          </Button>
        </div>
      </div>
    </div>
  );
}
