"use client";

import { AlertTriangle } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  isSubmitting?: boolean;
}

/** Shared confirmation modal for VIZU-Mock's persistent "Yakunlash"
 * button (see step-shell.tsx) — used identically by Lesen, Hören,
 * Schreiben and Sprechen instead of each step re-implementing its own
 * overlay/card markup. Confirming always triggers that step's own
 * existing submit path (server-side grading already treats an
 * unanswered question as incorrect/0 points — see lesen_service.py /
 * hoeren_service.py — so ending early needs no new backend logic). */
export default function VizuMockFinishConfirmDialog({ open, onCancel, onConfirm, isSubmitting }: Props) {
  const { t } = useTranslation();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-sm space-y-4 rounded-2xl bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border">
        <div className="flex items-start gap-3">
          <AlertTriangle size={20} className="mt-0.5 shrink-0 text-warning" />
          <div>
            <p className="text-sm font-bold text-text-primary">{t("vizuMock.finishConfirmTitle")}</p>
            <p className="mt-1 text-sm text-text-secondary">{t("vizuMock.finishConfirmBody")}</p>
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            {t("vizuMock.schreibenConfirmCancel")}
          </Button>
          <Button onClick={onConfirm} disabled={isSubmitting}>
            {isSubmitting ? t("common.loading") : t("vizuMock.finishConfirmSubmit")}
          </Button>
        </div>
      </div>
    </div>
  );
}
