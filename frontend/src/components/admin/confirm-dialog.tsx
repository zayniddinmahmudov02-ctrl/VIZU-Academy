"use client";

import { AlertTriangle } from "lucide-react";

import { AdminButton } from "./admin-ui";
import FormDialog from "./form-dialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  onConfirm: () => void;
  isPending?: boolean;
}

export default function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  onConfirm,
  isPending,
}: Props) {
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
          <AdminButton variant="danger" onClick={onConfirm} disabled={isPending}>
            {isPending ? "Wird gelöscht..." : "Löschen"}
          </AdminButton>
        </>
      }
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--admin-danger)]/10">
          <AlertTriangle size={18} className="text-[var(--admin-danger)]" />
        </div>
        <p className="text-sm text-[var(--admin-text-secondary)]">{description}</p>
      </div>
    </FormDialog>
  );
}
