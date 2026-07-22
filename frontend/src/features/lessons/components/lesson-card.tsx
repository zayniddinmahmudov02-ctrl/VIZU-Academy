"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Clock3, PlayCircle } from "lucide-react";

import { scaleOnHover } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import type { Lesson } from "../types/lesson";

interface Props {
  lesson: Lesson;
}

export default function LessonCard({ lesson }: Props) {
  const { t } = useTranslation();

  return (
    <motion.div {...scaleOnHover} className="h-full">
      <Link
        href={`/lessons/${lesson.id}`}
        className="flex h-full flex-col rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border transition-shadow duration-200 hover:shadow-[var(--shadow-lg)]"
      >
        <div className="flex items-center justify-between">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-accent-blue to-purple-600 text-white shadow-md">
            <PlayCircle size={22} />
          </div>
          <span className="rounded-full bg-accent-blue/10 px-3 py-1 text-xs font-bold text-accent-blue">
            {lesson.progress}%
          </span>
        </div>

        <h2 className="mt-5 flex-1 text-lg font-bold text-text-primary">{lesson.title}</h2>

        <div className="mt-5 flex items-center gap-2 text-sm text-text-muted">
          <Clock3 size={16} />
          {t("lessons.minutes", { count: lesson.duration })}
        </div>
      </Link>
    </motion.div>
  );
}
