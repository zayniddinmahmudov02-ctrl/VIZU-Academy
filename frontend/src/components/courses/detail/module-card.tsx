"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Lock } from "lucide-react";

interface Props {
  number: number;
  title: string;
  lessons: number;
  locked: boolean;
  href: string;
}

export default function ModuleCard({
  number,
  title,
  locked,
  href,
}: Props) {
  return (
    <motion.div
      whileHover={locked ? undefined : { y: -3 }}
      transition={{ duration: 0.2 }}
    >
      <Link
        href={locked ? "#" : href}
        aria-disabled={locked}
        className={`group flex items-center justify-between rounded-2xl border p-5 transition-all duration-300 ${
          locked
            ? "border-slate-200 bg-slate-100 opacity-70 dark:border-slate-700 dark:bg-slate-800"
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
          </div>
        </div>

        {locked ? (
          <div className="rounded-full bg-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 dark:bg-slate-700 dark:text-slate-200">
            Gesperrt
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-full bg-[var(--accent-gold)] px-4 py-2 text-sm font-semibold text-white transition-all group-hover:scale-105">
            Start
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