"use client";

import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

interface Props {
  /** e.g. "Aufgabe 7 / 20" — already translated. */
  positionLabel: string;
  answered: number;
  total: number;
  /** Minimum answered items needed before the competency can be submitted. */
  minRequired: number;
}

/** Position, answered count, the "at least N" requirement and a smoothly
 * animated progress bar (answered / total). Reduced motion is honoured via
 * the MotionConfig in app/(dashboard)/vizu-multilevel/layout.tsx. */
export default function VizuMultilevelProgressHeader({ positionLabel, answered, total, minRequired }: Props) {
  const { t } = useTranslation();
  const percent = total > 0 ? Math.round((answered / total) * 100) : 0;
  const minReached = answered >= minRequired;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-semibold">
        <span className="uppercase tracking-wide text-slate-500 dark:text-slate-400">{positionLabel}</span>
        <span className="tabular-nums text-slate-600 dark:text-slate-300">
          {t("vizuMultilevel.answeredOf", { answered, total })} · {percent}%
        </span>
      </div>

      <div
        className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={answered}
      >
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-orange-500 to-orange-400"
          initial={false}
          animate={{ width: `${percent}%` }}
          transition={{ type: "spring", stiffness: 220, damping: 30 }}
        />
      </div>

      {minRequired > 0 && (
        <p
          className={cn(
            "flex items-center gap-1.5 text-xs font-medium",
            minReached ? "text-emerald-600 dark:text-emerald-400" : "text-slate-500 dark:text-slate-400",
          )}
        >
          {minReached && <CheckCircle2 size={13} />}
          {minReached
            ? t("vizuMultilevel.minReached")
            : t("vizuMultilevel.minRequired", { answered: Math.min(answered, minRequired), min: minRequired })}
        </p>
      )}
    </div>
  );
}
