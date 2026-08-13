"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen } from "lucide-react";

import Badge from "@/components/ui/badge";
import ProgressBar from "@/components/ui/progress-bar";
import type { CourseWithLessonCount } from "@/features/courses/hooks/use-courses-with-lesson-counts";
import { scaleOnHover } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";

// Presentation only — gradient/chip colors per CEFR level code. Not a
// source of truth for which levels exist or their lesson counts (that's
// `course`, fetched live); levels not listed here just fall back to a
// neutral gradient rather than being hidden.
const LEVEL_STYLE: Record<string, { gradient: string }> = {
  A1: { gradient: "from-emerald-500 to-emerald-400" },
  A2: { gradient: "from-brand-500 to-brand-400" },
  B1: { gradient: "from-brand-700 to-brand-500" },
  B2: { gradient: "from-purple-600 to-purple-500" },
  C1: { gradient: "from-brand-900 to-brand-700" },
};
const DEFAULT_GRADIENT = "from-brand-600 to-accent-blue";

interface Props {
  course: CourseWithLessonCount;
  progress?: number;
}

export default function CourseCard({ course, progress = 0 }: Props) {
  const { t } = useTranslation();
  const gradient = LEVEL_STYLE[course.level]?.gradient ?? DEFAULT_GRADIENT;

  return (
    <motion.div {...scaleOnHover} className="h-full">
      <Link
        href={`/courses/${course.level.toLowerCase()}`}
        className="group flex h-full flex-col overflow-hidden rounded-card bg-surface-card shadow-[var(--shadow-md)] ring-1 ring-surface-border transition-shadow duration-200 hover:shadow-[var(--shadow-lg)]"
      >
        {/* Gradient illustration band */}
        <div className={`relative h-28 overflow-hidden bg-gradient-to-br ${gradient}`}>
          <div className="absolute -right-6 -top-10 h-32 w-32 rounded-full bg-white/15 blur-xl" />
          <div className="absolute -bottom-8 left-8 h-24 w-24 rounded-full bg-white/10 blur-lg" />
          <div className="absolute inset-0 flex items-center justify-between px-6">
            <span className="text-4xl font-bold text-white drop-shadow-sm">{course.level}</span>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/20 text-white backdrop-blur-md">
              <BookOpen size={22} />
            </div>
          </div>
        </div>

        <div className="flex flex-1 flex-col p-6">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-base font-bold text-text-primary">{course.title}</h2>
            {progress === 0 && <Badge variant="brand">{t("courses.newBadge")}</Badge>}
          </div>
          <p className="mt-1 text-sm text-text-secondary">{course.lessonCount} Lektionen</p>

          <div className="mt-5">
            <ProgressBar value={progress} />
            <p className="mt-2 text-xs font-medium text-text-secondary">
              {t("courses.percentDone", { count: progress })}
            </p>
          </div>

          <div className="mt-5 flex items-center justify-between gap-2 rounded-button bg-surface-hover px-4 py-2.5 text-sm font-semibold text-text-primary transition-colors group-hover:bg-accent-blue group-hover:text-white">
            {progress > 0 ? t("common.fortsetzen") : t("common.starten")}
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
