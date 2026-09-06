"use client";

import { ReactNode } from "react";
import { Dialog } from "@base-ui/react/dialog";

import { cn } from "@/lib/utils";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
  side?: "left" | "right";
  className?: string;
};

/** A left/right sliding overlay panel (mobile navigation, filters, ...). */
export default function Drawer({ open, onOpenChange, children, side = "left", className }: Props) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal keepMounted>
        <Dialog.Backdrop
          className={cn(
            "fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity duration-300",
            open ? "opacity-100" : "pointer-events-none opacity-0",
          )}
        />
        <Dialog.Popup
          className={cn(
            // fixed + h-full reaches the true viewport edges, so unlike
            // normal-flow content it isn't covered by body's safe-area
            // padding (globals.css) — needs its own, since the header/
            // close button (top) and language switcher (bottom, see
            // mobile-nav.tsx) must clear the iPhone notch/home indicator.
            "safe-top safe-bottom fixed top-0 z-50 h-full w-[260px] bg-surface-sidebar shadow-[var(--shadow-lg)] outline-none transition-transform duration-300 ease-out",
            side === "left"
              ? cn("left-0", open ? "translate-x-0" : "-translate-x-full")
              : cn("right-0", open ? "translate-x-0" : "translate-x-full"),
            className,
          )}
        >
          {children}
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
