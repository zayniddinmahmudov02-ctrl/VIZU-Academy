"use client";

import { motion } from "framer-motion";

import Logo from "@/components/common/logo";
import ProgressCircle from "@/components/ui/progress-circle";
import { fadeInUp } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function DashboardHero() {
  const { t } = useTranslation();
  // Overall progress = 0 until real cross-course analytics exist.
  const overallProgress = 0;

  return (
    <motion.section
      variants={fadeInUp}
      initial="hidden"
      animate="show"
      className="pattern-accent relative overflow-hidden rounded-card border border-accent-gold/20 bg-gradient-to-br from-surface-card via-[#fbf3de] to-surface-card px-6 py-7 shadow-[var(--shadow-card)] sm:px-9 sm:py-8"
    >
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-8">
        <div className="max-w-md">
          <h1 className="text-2xl font-bold leading-tight tracking-tight text-text-primary sm:text-[28px]">
            {t("dashboard.welcomeBack")}
            <br />
            <span className="text-accent-gold">Username!</span> 👋
          </h1>

          <p className="mt-3 text-sm leading-relaxed text-text-secondary">
            {t("dashboard.heroSubtitle")}
          </p>
        </div>

        <div className="flex items-center gap-6">
          <ProgressCircle
            value={overallProgress}
            size={92}
            strokeWidth={8}
            className="hidden sm:inline-flex"
          >
            <div className="text-center">
              <p className="text-lg font-bold text-text-primary">
                {overallProgress}%
              </p>

              <p className="text-[9px] font-medium leading-tight text-text-muted">
                {t("dashboard.overallProgressLine1")}
                <br />
                {t("dashboard.overallProgressLine2")}
              </p>
            </div>
          </ProgressCircle>

          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="hidden rounded-2xl bg-white/40 px-6 py-5 shadow-[var(--shadow-3d-soft)] ring-1 ring-accent-gold/25 backdrop-blur-sm md:flex"
          >
            <Logo
              size={64}
              showText
              orientation="stack"
              tagline
              dark={false}
            />
          </motion.div>
        </div>
      </div>
    </motion.section>
  );
}