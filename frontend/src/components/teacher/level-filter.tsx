"use client";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export const ALL_LEVELS = "ALL";

const LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2", "Multilevel"];

export function levelSortKey(level: string): number {
  const i = LEVEL_ORDER.indexOf(level);
  return i === -1 ? LEVEL_ORDER.length : i;
}

interface Props {
  /** Every level that can be shown (fixed set, so an empty level is still
   * a visible — if empty — bucket rather than silently missing). */
  levels: readonly string[];
  /** Number of submissions per level, for the count badges. */
  counts: Record<string, number>;
  active: string;
  onChange: (level: string) => void;
}

/** Teacher-panel level switcher: one chip per level with its submission
 * count, so submissions of different levels/sources are reviewed as
 * separate lists instead of one mixed queue. */
export default function LevelFilter({ levels, counts, active, onChange }: Props) {
  const { t } = useTranslation();
  const total = Object.values(counts).reduce((sum, n) => sum + n, 0);

  return (
    <div className="flex gap-1.5 overflow-x-auto rounded-xl bg-surface-hover p-1 ring-1 ring-surface-border">
      {[ALL_LEVELS, ...levels].map((level) => {
        const count = level === ALL_LEVELS ? total : (counts[level] ?? 0);
        return (
          <button
            key={level}
            type="button"
            onClick={() => onChange(level)}
            className={cn(
              "min-h-11 shrink-0 whitespace-nowrap rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors",
              active === level ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
            )}
          >
            {level === ALL_LEVELS ? t("teacher.allLevels") : level}
            <span className={cn("ml-1.5", active === level ? "text-white/80" : "text-text-muted")}>{count}</span>
          </button>
        );
      })}
    </div>
  );
}
