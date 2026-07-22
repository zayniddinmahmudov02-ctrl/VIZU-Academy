"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, PlayCircle } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import MosqueIllustration from "./mosque-illustration";
import { germanLevels } from "@/constants/levels";
import { useTranslation } from "@/lib/i18n/use-translation";
import {
  cardEntrance,
  fadeInUp,
  scaleOnHover,
  staggerContainer,
} from "@/lib/motion";

export default function ContinueLearning() {
  const { t } = useTranslation();
  const current = germanLevels[0];
  const progress = 0;

  return (
    <motion.section variants={fadeInUp} initial="hidden" animate="show">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-base font-bold text-text-primary">
          {t("dashboard.continueLearning")}
        </h2>

        <Link
          href="/courses"
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-accent-blue transition-colors hover:text-accent-blue-hover"
        >
          {t("dashboard.allCourses")}
          <ArrowRight size={15} />
        </Link>
      </div>

      <motion.div {...scaleOnHover}>
        <Link
          href={`/courses/${current.code.toLowerCase()}`}
          className={`group relative flex flex-col gap-8 overflow-hidden rounded-card bg-gradient-to-br ${current.gradient} p-7 text-white shadow-[var(--shadow-card)] transition-all duration-300 hover:shadow-[var(--shadow-card-hover)] sm:flex-row sm:items-center sm:justify-between sm:p-8`}
        >
          <div className="pointer-events-none absolute -bottom-4 right-5 opacity-20">
            <MosqueIllustration className="h-24 w-32" />
          </div>

          <div className="relative z-10 flex items-center gap-5">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white/15 shadow-[var(--shadow-3d-soft)] backdrop-blur-md">
              <PlayCircle size={26} />
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-white/70">
                {current.code} · {t(current.labelKey)}
              </p>

              <h3 className="mt-1 text-2xl font-bold">
                {t("dashboard.lessonTitle")}
              </h3>

              <p className="mt-2 text-sm text-white/75">
                {t("dashboard.lessonsAvailable", { count: current.modules })}
              </p>
            </div>
          </div>

          <div className="relative z-10 w-full sm:w-64">
            <div className="flex items-center justify-between text-sm font-medium text-white/90">
              <span>{t("dashboard.progressLabel")}</span>
              <span>{progress}%</span>
            </div>

            <ProgressBar
              value={progress}
              className="mt-3"
              trackClassName="h-2 bg-white/20"
              indicatorClassName="from-white to-white/80"
            />

            <div className="mt-5 flex justify-end">
              <span className="inline-flex items-center gap-2 rounded-full bg-black/20 px-5 py-2.5 text-sm font-semibold shadow-[var(--shadow-3d-soft)] transition-colors group-hover:bg-black/30">
                {progress > 0 ? t("common.fortsetzen") : t("dashboard.jetztStarten")}
                <ArrowRight
                  size={16}
                  className="transition-transform group-hover:translate-x-1"
                />
              </span>
            </div>
          </div>
        </Link>
      </motion.div>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="mt-6 grid grid-cols-2 gap-5 sm:grid-cols-3 xl:grid-cols-5"
      >
        {germanLevels.map((level) => (
          <motion.div
            key={level.code}
            variants={cardEntrance}
            whileHover={{ scale: 1.03, y: -3 }}
            transition={{ duration: 0.2 }}
          >
            <Link
              href={`/courses/${level.code.toLowerCase()}`}
              className={`block rounded-2xl p-5 shadow-[var(--shadow-card)] transition-all duration-300 hover:shadow-[var(--shadow-card-hover)] ${level.chip}`}
            >
              <span className="text-xl font-bold">
                {level.code}
              </span>

              <p className="mt-2 text-sm font-semibold opacity-90">
                {t(level.labelKey)}
              </p>

              <p className="mt-1 text-xs opacity-70">
                {t("dashboard.lessonsCount", { count: level.modules })}
              </p>
            </Link>
          </motion.div>
        ))}
      </motion.div>
    </motion.section>
  );
}