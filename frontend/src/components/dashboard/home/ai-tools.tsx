"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, BookText, GraduationCap } from "lucide-react";

import { cardEntrance, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";

const tools = [
  {
    titleKey: "dashboard.mockExams",
    subtitleKey: "dashboard.mockExamsSubtitle",
    href: "/vorbereitung",
    icon: GraduationCap,
    gradient: "from-purple-600 to-accent-purple",
  },
  {
    titleKey: "sidebar.dictionary",
    subtitleKey: "dashboard.woerterbuchSubtitle",
    href: "/woerterbuch",
    icon: BookText,
    gradient: "from-emerald-600 to-emerald-400",
  },
];

export default function AiTools() {
  const { t } = useTranslation();

  return (
    <section>
      <h2 className="mb-5 text-base font-bold text-text-primary">
        {t("dashboard.quickAccess")}
      </h2>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid gap-6 sm:grid-cols-2"
      >
        {tools.map((tool) => {
          const Icon = tool.icon;

          return (
            <motion.div
              key={tool.href}
              variants={cardEntrance}
              whileHover={{ y: -4, scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="h-full"
            >
              <Link
                href={tool.href}
                className={`group flex h-full min-h-[164px] flex-col overflow-hidden rounded-card bg-gradient-to-br p-5 text-white shadow-[var(--shadow-card)] transition-all duration-300 hover:shadow-[var(--shadow-card-hover)] ${tool.gradient}`}
              >
                <div className="flex flex-col gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 shadow-[var(--shadow-3d-soft)] backdrop-blur-sm">
                    <Icon size={16} />
                  </div>

                  <div>
                    <h3 className="text-lg font-bold">
                      {t(tool.titleKey)}
                    </h3>

                    <p className="mt-1 text-sm text-white/80">
                      {t(tool.subtitleKey)}
                    </p>
                  </div>
                </div>

                <div className="flex flex-1 items-center">
                  <span className="inline-flex w-fit items-center gap-2 rounded-full bg-black/20 px-4 py-2 text-sm font-semibold shadow-[inset_0_1px_0_rgba(255,255,255,0.2),inset_0_-2px_3px_rgba(0,0,0,0.2),0_4px_10px_-2px_rgba(0,0,0,0.3)] transition-all duration-200 group-hover:bg-black/30">
                    {t("common.starten")}
                    <ArrowRight
                      size={15}
                      className="transition-transform duration-200 group-hover:translate-x-1"
                    />
                  </span>
                </div>
              </Link>
            </motion.div>
          );
        })}
      </motion.div>
    </section>
  );
}