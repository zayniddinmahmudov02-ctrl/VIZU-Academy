"use client";

import { useState } from "react";
import { motion } from "framer-motion";

import { useTranslation } from "@/lib/i18n/use-translation";

const levels = ["Alle", "A1", "A2", "B1", "B2", "C1"];

export default function CourseFilter() {
  const { t } = useTranslation();
  const [active, setActive] = useState("Alle");

  return (
    <div className="flex flex-wrap gap-2">
      {levels.map((level) => {
        const isActive = active === level;
        const label = level === "Alle" ? t("courses.filterAll") : level;

        return (
          <button
            key={level}
            type="button"
            onClick={() => setActive(level)}
            className={`relative rounded-full px-4 py-2 text-xs font-semibold transition-colors ${
              isActive
                ? "text-white"
                : "bg-surface-card text-text-secondary ring-1 ring-surface-border hover:text-text-primary"
            }`}
          >
            {isActive && (
              <motion.span
                layoutId="course-filter-pill"
                transition={{ type: "spring", stiffness: 420, damping: 36 }}
                className="absolute inset-0 rounded-full bg-gradient-to-r from-accent-blue to-purple-600"
              />
            )}
            <span className="relative z-10">{label}</span>
          </button>
        );
      })}
    </div>
  );
}
