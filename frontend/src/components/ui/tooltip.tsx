"use client";

import { ReactNode } from "react";
import { Tooltip as TooltipPrimitive } from "@base-ui/react/tooltip";
import { motion } from "framer-motion";

type Props = {
  label: string;
  children: ReactNode;
  disabled?: boolean;
  side?: "top" | "right" | "bottom" | "left";
};

export default function Tooltip({ label, children, disabled, side = "right" }: Props) {
  if (disabled) return <>{children}</>;

  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger render={<span>{children}</span>} />
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Positioner side={side} sideOffset={10}>
          <TooltipPrimitive.Popup
            render={
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.12 }}
                className="rounded-lg bg-text-primary px-2.5 py-1.5 text-xs font-semibold text-surface-bg shadow-[var(--shadow-md)]"
              />
            }
          >
            {label}
          </TooltipPrimitive.Popup>
        </TooltipPrimitive.Positioner>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}
