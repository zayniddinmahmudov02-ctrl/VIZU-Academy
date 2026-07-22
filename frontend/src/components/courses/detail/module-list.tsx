"use client";

import { motion } from "framer-motion";

import { COURSE_CONTENT } from "@/constants/course-content";
import type { LevelCode } from "@/constants/levels";
import { cardEntrance, staggerContainer } from "@/lib/motion";

import ModuleCard from "./module-card";

interface Props {
  level: LevelCode;
}

export default function ModuleList({ level }: Props) {
  const lessons = COURSE_CONTENT[level].lessons;

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

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="space-y-4"
      >
        {lessons.map((lesson, index) => (
          <motion.div
            key={lesson.number}
            variants={cardEntrance}
          >
            <ModuleCard
              number={lesson.number}
              title={lesson.title}
              lessons={0}
              locked={index !== 0}
            />
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}