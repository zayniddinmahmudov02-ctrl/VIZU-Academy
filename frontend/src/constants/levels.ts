/**
 * German course levels (CEFR) and their module counts.
 * Source of truth for the VIZU Academy German track.
 */
export type LevelCode = "A1" | "A2" | "B1" | "B2" | "C1";

export interface LevelInfo {
  code: LevelCode;
  modules: number;
  /** Translation key (in the "levels" namespace) for the level's display name. */
  labelKey: string;
  gradient: string;
  /** Pastel bg + text classes for the dashboard's level-chip row. */
  chip: string;
}

export const germanLevels: LevelInfo[] = [
  {
    code: "A1",
    modules: 14,
    labelKey: "levels.a1",
    gradient: "from-emerald-500 to-emerald-400",
    chip:
      "bg-emerald-50 text-emerald-900 ring-1 ring-emerald-200 dark:bg-emerald-900/30 dark:text-white dark:ring-emerald-500/30",
  },
  {
    code: "A2",
    modules: 14,
    labelKey: "levels.a2",
    gradient: "from-brand-500 to-brand-400",
    chip:
      "bg-blue-50 text-blue-900 ring-1 ring-blue-200 dark:bg-blue-900/30 dark:text-white dark:ring-blue-500/30",
  },
  {
    code: "B1",
    modules: 20,
    labelKey: "levels.b1",
    gradient: "from-brand-700 to-brand-500",
    chip:
      "bg-violet-50 text-violet-900 ring-1 ring-violet-200 dark:bg-violet-900/30 dark:text-white dark:ring-violet-500/30",
  },
  {
    code: "B2",
    modules: 30,
    labelKey: "levels.b2",
    gradient: "from-purple-600 to-purple-500",
    chip:
      "bg-pink-50 text-pink-900 ring-1 ring-pink-200 dark:bg-pink-900/30 dark:text-white dark:ring-pink-500/30",
  },
  {
    code: "C1",
    modules: 22,
    labelKey: "levels.c1",
    gradient: "from-brand-900 to-brand-700",
    chip:
      "bg-rose-100 text-yellow-700 ring-1 ring-yellow-300 dark:bg-rose-900/30 dark:text-white dark:ring-rose-500/30",
  },
];

export const totalGermanModules = germanLevels.reduce(
  (sum, level) => sum + level.modules,
  0,
);