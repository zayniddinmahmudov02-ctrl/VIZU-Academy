"use client";

import { LogOut, X } from "lucide-react";

import Drawer from "@/components/ui/drawer";
import Logo from "@/components/common/logo";
import { sidebarItems } from "@/constants/sidebar";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { useTranslation } from "@/lib/i18n/use-translation";
import NavItem from "../navigation/nav-item";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export default function MobileNav({ open, onOpenChange }: Props) {
  const { t } = useTranslation();
  const logout = useLogout();

  return (
    <Drawer open={open} onOpenChange={onOpenChange} side="left">
      <div className="flex h-full flex-col">
        <div className="flex h-20 items-center justify-between border-b border-white/10 px-5">
          <Logo size={36} dark />
          <button
            onClick={() => onOpenChange(false)}
            aria-label={t("sidebar.closeMenu")}
            className="flex h-9 w-9 items-center justify-center rounded-full text-white/60 transition-colors hover:bg-white/[0.08] hover:text-white"
          >
            <X size={16} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5" onClick={() => onOpenChange(false)}>
          {sidebarItems.map((item) => (
            <NavItem key={item.href} {...item} />
          ))}
        </nav>

        <div className="border-t border-white/10 p-3">
          <button
            type="button"
            onClick={() => {
              onOpenChange(false);
              logout();
            }}
            data-testid="mobile-logout"
            className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold text-red-300 transition-colors hover:bg-white/[0.08] hover:text-red-200"
          >
            <LogOut size={18} aria-hidden="true" />
            {t("header.logout")}
          </button>
        </div>
      </div>
    </Drawer>
  );
}
