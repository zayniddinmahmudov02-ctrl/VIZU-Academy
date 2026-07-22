"use client";

import { Progress } from "@base-ui/react/progress";
import { motion } from "framer-motion";

import { cn } from "@/lib/utils";

type Props = {
  value: number;
  className?: string;
  trackClassName?: string;
  indicatorClassName?: string;
};

export default function ProgressBar({
  value,
  className,
  trackClassName,
  indicatorClassName,
}: Props) {
  return (
    <Progress.Root
      value={value}
      getAriaValueText={(_, v) => `${v ?? 0}%`}
      className={cn("w-full", className)}
    >
      <Progress.Track
        className={cn(
          "relative h-2 w-full overflow-hidden rounded-full bg-surface-hover",
          trackClassName,
        )}
      >
        <Progress.Indicator
          render={
            <motion.div
              className={cn(
                "h-full rounded-full bg-gradient-to-r from-accent-blue to-accent-purple",
                indicatorClassName,
              )}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          }
        />
      </Progress.Track>
    </Progress.Root>
  );
}
