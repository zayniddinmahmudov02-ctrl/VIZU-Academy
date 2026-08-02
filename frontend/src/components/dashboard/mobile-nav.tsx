"use client";

import { X } from "lucide-react";

import Drawer from "@/components/ui/drawer";
import Logo from "@/components/common/logo";
import { useSidebarItems } from "@/hooks/use-sidebar-items";
import { useTranslation } from "@/lib/i18n/use-translation";
import NavItem from "../navigation/nav-item";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export default function MobileNav({ open, onOpenChange }: Props) {
  const { t } = useTranslation();
  const sidebarItems = useSidebarItems();

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
      </div>
    </Drawer>
  );
}
