"use client";

import { ReactNode } from "react";
import { Popover as PopoverPrimitive } from "@base-ui/react/popover";
import { motion } from "framer-motion";

type Props = {
  trigger: ReactNode;
  children: ReactNode;
  align?: "start" | "center" | "end";
};

export default function Popover({ trigger, children, align = "end" }: Props) {
  return (
    <PopoverPrimitive.Root>
      <PopoverPrimitive.Trigger className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/40">
        {trigger}
      </PopoverPrimitive.Trigger>
      <PopoverPrimitive.Portal>
        <PopoverPrimitive.Positioner align={align} sideOffset={10} className="z-50 outline-none">
          <PopoverPrimitive.Popup
            render={
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -6 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className="w-80 overflow-hidden rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-lg)] ring-1 ring-surface-border"
              />
            }
          >
            {children}
          </PopoverPrimitive.Popup>
        </PopoverPrimitive.Positioner>
      </PopoverPrimitive.Portal>
    </PopoverPrimitive.Root>
  );
}
