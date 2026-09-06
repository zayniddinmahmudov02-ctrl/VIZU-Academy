"use client";

import { Dialog } from "@base-ui/react/dialog";

import AdminSidebar from "./admin-sidebar";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function AdminMobileNav({ open, onOpenChange }: Props) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal keepMounted>
        <Dialog.Backdrop
          className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${
            open ? "opacity-100" : "pointer-events-none opacity-0"
          }`}
        />
        <Dialog.Popup
          // safe-top/safe-bottom: this is fixed + h-full, reaching the
          // true viewport edges — not covered by body's safe-area
          // padding (globals.css), so its own header/nav must clear the
          // notch/home indicator explicitly.
          className={`admin-shell safe-top safe-bottom fixed left-0 top-0 z-50 h-full w-[270px] shadow-[var(--admin-shadow-card)] outline-none transition-transform duration-300 ease-out ${
            open ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <AdminSidebar className="w-full" />
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
