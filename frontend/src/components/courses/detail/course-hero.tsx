"use client";

import { BookOpen, GraduationCap, Layers3, Trophy } from "lucide-react";

import { useLevelCourse } from "@/features/courses/hooks/use-level-course";
import type { LevelCode } from "@/constants/levels";

interface Props {
  level: LevelCode;
  progress?: number;
  unlockedLessons?: number;
}

export default function CourseHero({
  level,
  progress = 0,
  unlockedLessons = 1,
}: Props) {
  const { course, lessons } = useLevelCourse(level);

  if (!course) return null;

  return (
    <section className="relative overflow-hidden rounded-card bg-gradient-to-br from-brand-700 via-accent-blue to-purple-600 p-8 text-white shadow-[var(--shadow-lg)] sm:p-10">
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 left-1/3 h-64 w-64 rounded-full bg-purple-300/20 blur-3xl" />

      <div className="relative z-10 flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="inline-flex items-center gap-2.5 rounded-full bg-white/15 px-4 py-2 backdrop-blur-md">
            <GraduationCap size={17} />
            <span className="text-sm font-semibold">
              {course.level} Kurs
            </span>
          </div>

          <h1 className="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">
            {course.title}
          </h1>

          <p className="mt-3 max-w-xl text-sm leading-relaxed text-white/80 sm:text-base">
            {course.description}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-2xl bg-white/10 p-5 backdrop-blur-md transition hover:bg-white/15">
            <Layers3 size={18} />
            <h3 className="mt-3 text-3xl font-bold">
              {lessons.length}
            </h3>
            <p className="mt-1 text-sm text-white/70">
              Unterricht
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 p-5 backdrop-blur-md transition hover:bg-white/15">
            <BookOpen size={18} />
            <h3 className="mt-3 text-3xl font-bold">
              {unlockedLessons}
            </h3>
            <p className="mt-1 text-sm text-white/70">
              Freigeschaltet
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 p-5 backdrop-blur-md transition hover:bg-white/15">
            <Trophy size={18} />
            <h3 className="mt-3 text-3xl font-bold">
              {progress}%
            </h3>
            <p className="mt-1 text-sm text-white/70">
              Fortschritt
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}