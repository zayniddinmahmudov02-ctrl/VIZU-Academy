"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, BookText, Gauge, GraduationCap } from "lucide-react";

import BattleBanner from "@/components/dashboard/home/battle-banner";
import { cardEntrance, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";

const tools = [
  {
    titleKey: "dashboard.vizuMultilevelTitle",
    subtitleKey: "dashboard.vizuMultilevelSubtitle",
    ariaKey: "dashboard.vizuMultilevelAria",
    ctaKey: "dashboard.vizuMultilevelCta",
    href: "/vizu-multilevel",
    icon: Gauge,
    gradient: "from-accent-blue to-blue-500",
  },
  {
    titleKey: "dashboard.woerterbuchTitle",
    subtitleKey: "dashboard.woerterbuchSubtitle",
    ariaKey: "dashboard.woerterbuchAria",
    ctaKey: "dashboard.woerterbuchCta",
    href: "/woerterbuch",
    icon: BookText,
    gradient: "from-emerald-600 to-emerald-400",
  },
  {
    titleKey: "dashboard.mockExams",
    subtitleKey: "dashboard.mockExamsSubtitle",
    ariaKey: "dashboard.mockExamsAria",
    ctaKey: "dashboard.mockExamsCta",
    href: "/vorbereitung",
    icon: GraduationCap,
    gradient: "from-purple-600 to-accent-purple",
  },
];

export default function LearningTools() {
  const { t } = useTranslation();

  return (
    <section aria-labelledby="learning-tools-title" data-testid="dashboard-learning-tools">
      <h2 id="learning-tools-title" className="mb-3 text-base font-bold text-text-primary">
        {t("dashboard.learningTools")}
      </h2>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid auto-rows-fr grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4"
      >
        <motion.div
          variants={cardEntrance}
          whileHover={{ y: -3, scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          className="h-full"
        >
          <BattleBanner />
        </motion.div>

        {tools.map((tool) => {
          const Icon = tool.icon;

          return (
            <motion.div
              key={tool.href}
              variants={cardEntrance}
              whileHover={{ y: -3, scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="h-full"
            >
              <Link
                href={tool.href}
                prefetch={false}
                aria-label={t(tool.ariaKey)}
                className={`group flex h-full min-h-[204px] min-w-0 flex-col overflow-hidden rounded-card bg-gradient-to-br p-4 text-white shadow-[var(--shadow-card)] transition-shadow duration-200 hover:shadow-[var(--shadow-card-hover)] ${tool.gradient}`}
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20 shadow-[var(--shadow-3d-soft)]">
                  <Icon size={17} aria-hidden="true" />
                </div>

                <div className="mt-3">
                  <h3 className="break-words text-sm font-bold leading-snug sm:text-base">
                    {t(tool.titleKey)}
                  </h3>
                  <p className="mt-1 text-xs leading-relaxed text-white/85 sm:text-sm">
                    {t(tool.subtitleKey)}
                  </p>
                </div>

                <span className="mt-auto inline-flex min-h-10 w-fit max-w-full items-center gap-2 pt-3 text-sm font-bold">
                  <span>{t(tool.ctaKey)}</span>
                  <ArrowRight
                    size={15}
                    aria-hidden="true"
                    className="shrink-0 transition-transform duration-200 group-hover:translate-x-1"
                  />
                </span>
              </Link>
            </motion.div>
          );
        })}
      </motion.div>
    </section>
  );
}
