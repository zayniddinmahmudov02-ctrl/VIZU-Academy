"use client";

import { useState } from "react";

import { AdminButton, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import type { AdminOrderItem } from "@/features/admin/types/vizu-pay.types";

const REASON_PRESETS = [
  "Beleg ist unklar",
  "Zahlungsbetrag ist falsch",
  "Falsche Karte",
  "Doppelte Zahlung",
  "Ungültiger Beleg",
  "Zahlung konnte nicht verifiziert werden",
  "Andere",
] as const;

interface Props {
  order: AdminOrderItem | null;
  onClose: () => void;
  onConfirm: (reason: string) => void;
  isPending: boolean;
}

export default function RejectDialog({ order, onClose, onConfirm, isPending }: Props) {
  const [preset, setPreset] = useState<string>(REASON_PRESETS[0]);
  const [customReason, setCustomReason] = useState("");

  const reason = preset === "Andere" ? customReason.trim() : preset;
  const buyerName = order ? [order.user_first_name, order.user_last_name].filter(Boolean).join(" ") || order.user_username : "";

  function handleClose(open: boolean) {
    if (!open) {
      setPreset(REASON_PRESETS[0]);
      setCustomReason("");
      onClose();
    }
  }

  return (
    <FormDialog
      open={!!order}
      onOpenChange={handleClose}
      title={`Zahlung ablehnen — ${buyerName}`}
      footer={
        <>
          <AdminButton variant="ghost" onClick={() => handleClose(false)}>
            Abbrechen
          </AdminButton>
          <AdminButton variant="danger" onClick={() => onConfirm(reason)} disabled={!reason || isPending}>
            {isPending ? "Wird abgelehnt..." : "Ablehnen"}
          </AdminButton>
        </>
      }
    >
      <div className="space-y-4">
        <div>
          <AdminLabel>Ablehnungsgrund</AdminLabel>
          <AdminSelect value={preset} onChange={(e) => setPreset(e.target.value)}>
            {REASON_PRESETS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </AdminSelect>
        </div>

        {preset === "Andere" && (
          <div>
            <AdminLabel>Grund (erforderlich)</AdminLabel>
            <AdminTextarea
              rows={3}
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              placeholder="Grund beschreiben..."
            />
          </div>
        )}
      </div>
    </FormDialog>
  );
}
