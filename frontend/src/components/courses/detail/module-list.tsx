"use client";

import { motion } from "framer-motion";

import type { LevelCode } from "@/constants/levels";
import { useLevelCourse } from "@/features/courses/hooks/use-level-course";
import { cardEntrance, staggerContainer } from "@/lib/motion";

import ModuleCard from "./module-card";

interface Props {
  level: LevelCode;
}

export default function ModuleList({ level }: Props) {
  const { lessons, isLoading } = useLevelCourse(level);
  const sorted = [...lessons].sort((a, b) => a.number - b.number);

  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-text-primary">
          Unterricht
        </h2>

        <p className="mt-1.5 text-text-secondary">
          Schließe einen Unterricht ab, um den nächsten freizuschalten.
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
        {sorted.map((lesson, index) => (
          <motion.div
            key={lesson.id}
            variants={cardEntrance}
          >
            <ModuleCard
              number={lesson.number}
              title={lesson.title}
              lessons={0}
              locked={index !== 0}
              href={`/lessons/${lesson.id}`}
            />
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}