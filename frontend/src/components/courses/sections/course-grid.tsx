"use client";

import CourseCard from "../cards/course-card";

import { useCoursesWithLessonCounts } from "@/features/courses/hooks/use-courses-with-lesson-counts";

export default function CourseGrid() {
  const { data: courses, isLoading } = useCoursesWithLessonCounts();

  if (isLoading) {
    return <p className="text-sm text-text-secondary">Wird geladen...</p>;
  }

  if (!courses || courses.length === 0) {
    return (
      <p className="rounded-card bg-surface-card p-6 text-center text-sm text-text-secondary shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
        Noch keine Kurse verfügbar.
      </p>
    );
  }

  return (
    <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
      {courses.map((course) => (
        <CourseCard key={course.id} course={course} />
      ))}
    </section>
  );
}
