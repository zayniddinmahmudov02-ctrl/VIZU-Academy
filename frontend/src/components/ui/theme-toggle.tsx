"use client";

import { Switch } from "@base-ui/react/switch";
import { motion } from "framer-motion";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { useHasMounted } from "@/hooks/use-mounted";
import { cn } from "@/lib/utils";

type Props = {
  className?: string;
  /** "switch" = labelled slider (sidebar footer). "icon" = round button matching the topbar icons. */
  variant?: "switch" | "icon";
};

export default function ThemeToggle({ className, variant = "switch" }: Props) {
  const { resolvedTheme, setTheme } = useTheme();
  const mounted = useHasMounted();

  const isDark = mounted && resolvedTheme === "dark";

  if (variant === "icon") {
    return (
      <button
        onClick={() => setTheme(isDark ? "light" : "dark")}
        aria-label="Theme umschalten"
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-full bg-surface-card text-text-secondary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:text-warning",
          className,
        )}
      >
        {isDark ? <Moon size={15} className="text-accent-purple" /> : <Sun size={15} className="text-warning" />}
      </button>
    );
  }

  return (
    <Switch.Root
      checked={isDark}
      onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
      aria-label="Toggle theme"
      className={cn(
        "relative inline-flex h-9 w-16 shrink-0 items-center rounded-full bg-surface-hover p-0.5 ring-1 ring-surface-border transition-colors duration-200",
        className,
      )}
    >
      <motion.span
        className="flex h-7 w-7 items-center justify-center rounded-full bg-surface-card shadow-md"
        animate={{ x: isDark ? 28 : 0 }}
        transition={{ type: "spring", stiffness: 500, damping: 32 }}
      >
        {isDark ? (
          <Moon size={14} className="text-accent-purple" strokeWidth={2.25} />
        ) : (
          <Sun size={14} className="text-warning" strokeWidth={2.25} />
        )}
      </motion.span>
    </Switch.Root>
  );
}
