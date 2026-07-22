"use client";

import { ReactNode } from "react";
import { Menu } from "@base-ui/react/menu";
import { motion } from "framer-motion";

import { cn } from "@/lib/utils";

export type DropdownMenuItem = {
  label: string;
  icon?: React.ElementType;
  onClick?: () => void;
  danger?: boolean;
};

type Props = {
  trigger: ReactNode;
  items: DropdownMenuItem[];
  align?: "start" | "center" | "end";
};

export default function DropdownMenu({ trigger, items, align = "end" }: Props) {
  return (
    <Menu.Root>
      <Menu.Trigger className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/40">
        {trigger}
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Positioner align={align} sideOffset={10} className="z-50 outline-none">
          <Menu.Popup
            render={
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -6 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className="min-w-[200px] overflow-hidden rounded-2xl bg-surface-card p-1.5 shadow-[var(--shadow-lg)] ring-1 ring-surface-border"
              />
            }
          >
            {items.map((item) => (
              <Menu.Item
                key={item.label}
                onClick={item.onClick}
                className={cn(
                  "flex cursor-pointer items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium text-text-primary outline-none transition-colors data-[highlighted]:bg-surface-hover",
                  item.danger && "text-danger data-[highlighted]:bg-danger/10",
                )}
              >
                {item.icon && <item.icon size={14} />}
                {item.label}
              </Menu.Item>
            ))}
          </Menu.Popup>
        </Menu.Positioner>
      </Menu.Portal>
    </Menu.Root>
  );
}
