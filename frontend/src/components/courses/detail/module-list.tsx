"use client";

import { motion } from "framer-motion";

import type { LevelCode } from "@/constants/levels";
import { useLevelCourse } from "@/features/courses/hooks/use-level-course";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cardEntrance, staggerContainer } from "@/lib/motion";

import ModuleCard from "./module-card";

interface Props {
  level: LevelCode;
}

export default function ModuleList({ level }: Props) {
  const { t } = useTranslation();
  const { lessons, isLoading } = useLevelCourse(level);
  const sorted = [...lessons].sort((a, b) => a.number - b.number);

  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-text-primary">
          Unterricht
        </h2>

        <p className="mt-1.5 text-text-secondary">
          {t("courses.lessonsSubtitle")}
        </p>
      </div>

      {isLoading && <p className="text-sm text-text-secondary">Wird geladen...</p>}

      {!isLoading && sorted.length === 0 && (
        <p className="rounded-card bg-surface-card p-6 text-center text-sm text-text-secondary shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
          Für dieses Niveau sind noch keine Lektionen verfügbar.
        </p>
      )}

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="space-y-4"
      >
        {sorted.map((lesson) => (
          <motion.div
            key={lesson.id}
            variants={cardEntrance}
          >
            <ModuleCard
              number={lesson.number}
              title={lesson.title}
              lessons={0}
              locked={lesson.isLocked}
              href={`/lessons/${lesson.id}`}
            />
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
