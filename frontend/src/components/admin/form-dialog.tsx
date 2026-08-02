"use client";

import { ReactNode } from "react";
import { Dialog } from "@base-ui/react/dialog";
import { X } from "lucide-react";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "md" | "lg" | "xl";
}

const SIZE_CLASS = {
  md: "max-w-md",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
};

export default function FormDialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  size = "md",
}: Props) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-200 data-[ending-style]:opacity-0 data-[starting-style]:opacity-0" />
        <Dialog.Popup
          className={`admin-shell fixed left-1/2 top-1/2 z-50 max-h-[90vh] w-[92vw] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl bg-[var(--admin-card)] p-6 shadow-[var(--admin-shadow-card)] outline-none ring-1 ring-[var(--admin-border-strong)] transition-all duration-200 data-[ending-style]:scale-95 data-[ending-style]:opacity-0 data-[starting-style]:scale-95 data-[starting-style]:opacity-0 sm:p-7 ${SIZE_CLASS[size]}`}
        >
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-lg font-bold text-[var(--admin-text-primary)]">
                {title}
              </Dialog.Title>
              {description && (
                <Dialog.Description className="mt-1 text-sm text-[var(--admin-text-secondary)]">
                  {description}
                </Dialog.Description>
              )}
            </div>
            <Dialog.Close
              aria-label="Schließen"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--admin-text-muted)] transition hover:bg-white/5 hover:text-[var(--admin-text-primary)]"
            >
              <X size={17} />
            </Dialog.Close>
          </div>

          <div>{children}</div>

          {footer && <div className="mt-6 flex items-center justify-end gap-3">{footer}</div>}
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
