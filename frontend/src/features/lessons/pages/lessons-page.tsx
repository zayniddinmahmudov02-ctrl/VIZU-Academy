"use client";

import { motion } from "framer-motion";

import Loading from "@/components/common/loading";
import ErrorState from "@/components/common/error";
import { cardEntrance, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonCard from "../components/lesson-card";
import { useLessons } from "../hooks/use-lessons";

export default function LessonsPage() {
  const { t } = useTranslation();
  const { lessons, loading, error } = useLessons();

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
          {t("lessons.title")}
        </h1>
        <p className="mt-2 text-text-secondary">{t("lessons.subtitle")}</p>
      </div>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3"
      >
        {lessons.map((lesson) => (
          <motion.div key={lesson.id} variants={cardEntrance}>
            <LessonCard lesson={lesson} />
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
