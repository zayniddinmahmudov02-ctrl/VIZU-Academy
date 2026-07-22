"use client";

import { motion } from "framer-motion";
import { Award, BookCheck, Clock3, Flame, TrendingUp } from "lucide-react";

import { cardEntrance, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";

const stats = [
  {
    labelKey: "dashboard.statLernzeit",
    value: "0h",
    deltaKey: "dashboard.deltaWeek",
    icon: Clock3,
    gradient: "from-accent-blue to-brand-400",
    spark: "M2 20 L14 17 L26 18 L38 12 L50 14 L62 6",
  },
  {
    labelKey: "dashboard.statUnterrichte",
    value: "0",
    deltaKey: "dashboard.deltaWeek",
    icon: BookCheck,
    gradient: "from-emerald-600 to-emerald-400",
    spark: "M2 18 L14 19 L26 14 L38 15 L50 9 L62 8",
  },
  {
    labelKey: "dashboard.statZertifikate",
    value: "0",
    deltaKey: "dashboard.deltaMonth",
    icon: Award,
    gradient: "from-purple-600 to-accent-purple",
    spark: "M2 16 L14 16 L26 16 L38 16 L50 16 L62 16",
  },
  {
    labelKey: "dashboard.statLernserie",
    value: "0 Tage",
    deltaKey: "dashboard.deltaStreak",
    icon: Flame,
    gradient: "from-warning to-amber-400",
    spark: "M2 20 L14 20 L26 20 L38 20 L50 20 L62 20",
  },
];

export default function StatsRow() {
  const { t } = useTranslation();

  return (
    <motion.section
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="grid grid-cols-2 gap-6 lg:grid-cols-4"
    >
      {stats.map((stat) => (
        <motion.div
          key={stat.labelKey}
          variants={cardEntrance}
          whileHover={{ y: -4 }}
          transition={{ duration: 0.25 }}
          className="relative flex min-h-[145px] flex-col justify-between overflow-hidden rounded-card bg-surface-card p-6 shadow-[var(--shadow-card)] ring-1 ring-surface-border transition-all duration-300 hover:shadow-[var(--shadow-card-hover)]"
        >
          <div className="flex items-start gap-4">
            <div
              className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br text-white shadow-[var(--shadow-3d-soft)] ${stat.gradient}`}
            >
              <stat.icon size={20} />
            </div>

            <div>
              <p className="text-xs font-semibold text-[#B8912B] dark:text-gray-300">
                {t(stat.labelKey)}
              </p>

              <p className="mt-2 text-3xl font-extrabold text-[#17203D] dark:text-white">
                {stat.value}
              </p>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <TrendingUp size={13} />
              {t(stat.deltaKey)}
            </span>

            <svg viewBox="0 0 64 24" className="h-5 w-16 opacity-70">
              <path
                d={stat.spark}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                className="text-[#D4AF37] dark:text-white"
              />
            </svg>
          </div>
        </motion.div>
      ))}
    </motion.section>
  );
}