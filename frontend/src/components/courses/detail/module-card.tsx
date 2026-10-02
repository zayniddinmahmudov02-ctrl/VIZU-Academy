"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Check, Lock } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  number: number;
  title: string;
  lessons: number;
  locked: boolean;
  /** The course's free first lesson (backend `is_free_lesson`). */
  free?: boolean;
  href: string;
}

export default function ModuleCard({
  number,
  title,
  locked,
  free = false,
  href,
}: Props) {
  const { t } = useTranslation();
  const target = locked ? "/angebote" : href;
  // Cosmetic only — only the course's first lesson is free; anything else
  // shown unlocked here was bought (Angebote). Actual access is enforced
  // server-side regardless of this label.
  const isInherentlyFree = free;

  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2 }}
    >
      <Link
        href={target}
        className={`group flex items-center justify-between rounded-2xl border p-5 transition-all duration-300 ${
          locked
            ? "border-slate-200 bg-slate-100 dark:border-slate-700 dark:bg-slate-800"
            : "border-[var(--surface-border)] bg-[var(--surface-card)] hover:border-[var(--accent-gold)] hover:shadow-xl"
        }`}
      >
        <div className="flex items-center gap-4">
          <div
            className={`flex h-14 w-14 items-center justify-center rounded-2xl ${
              locked
                ? "bg-slate-300 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                : "bg-gradient-to-br from-yellow-500 to-amber-400 text-white shadow-lg"
            }`}
          >
            {locked ? <Lock size={22} /> : <BookOpen size={22} />}
          </div>

          <div>
            <h3 className="text-lg font-bold text-text-primary">
              Unterricht {number}
            </h3>

            <p className="mt-1 text-sm text-text-secondary">
              {title}
            </p>

            <p
              className={`mt-1 flex items-center gap-1 text-xs font-medium ${
                locked ? "text-warning" : "text-success"
              }`}
            >
              {locked ? (
                <>
                  <Lock size={11} />
                  {t("courses.lessonPremium")}
                </>
              ) : (
                <>
                  <Check size={11} />
                  {isInherentlyFree ? t("courses.lessonFree") : t("courses.lessonUnlocked")}
                </>
              )}
            </p>
          </div>
        </div>

        {locked ? (
          <div className="flex items-center gap-2 rounded-full bg-warning/15 px-4 py-2 text-xs font-semibold text-warning transition-all group-hover:scale-105">
            {t("courses.unlockCourse")}
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-full bg-[var(--accent-gold)] px-4 py-2 text-sm font-semibold text-white transition-all group-hover:scale-105">
            {t("courses.lessonOpen")}
            <ArrowRight
              size={16}
              className="transition-transform group-hover:translate-x-1"
            />
          </div>
        )}
      </Link>
    </motion.div>
  );
}
