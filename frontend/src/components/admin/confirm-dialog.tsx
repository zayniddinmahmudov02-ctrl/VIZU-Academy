"use client";

import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { AdminButton } from "./admin-ui";
import FormDialog from "./form-dialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  onConfirm: () => void;
  isPending?: boolean;
  error?: string | null;
  /** Defaults keep the delete dialog unchanged; e.g. "Veröffentlichen" for a publish confirmation. */
  confirmLabel?: string;
  pendingLabel?: string;
  variant?: "danger" | "primary";
}

export default function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  onConfirm,
  isPending,
  error,
  confirmLabel = "Löschen",
  pendingLabel = "Wird gelöscht...",
  variant = "danger",
}: Props) {
  const danger = variant === "danger";
  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      size="md"
      footer={
        <>
          <AdminButton variant="ghost" onClick={() => onOpenChange(false)} disabled={isPending}>
            Abbrechen
          </AdminButton>
          <AdminButton variant={variant} onClick={onConfirm} disabled={isPending} data-testid="confirm-dialog-confirm">
            {isPending ? pendingLabel : confirmLabel}
          </AdminButton>
        </>
      }
    >
      <div className="flex items-start gap-3">
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${danger ? "bg-[var(--admin-danger)]/10" : "bg-[var(--admin-primary)]/10"}`}>
          {danger ? <AlertTriangle size={18} className="text-[var(--admin-danger)]" /> : <CheckCircle2 size={18} className="text-[var(--admin-primary)]" />}
        </div>
        <div>
          <p className="text-sm text-[var(--admin-text-secondary)]">{description}</p>
          {error && <p className="mt-2 text-sm text-[var(--admin-danger)]">{error}</p>}
        </div>
      </div>
    </FormDialog>
  );
}
