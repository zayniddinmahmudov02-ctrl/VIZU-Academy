"use client";

import { useQuery } from "@tanstack/react-query";

import CourseCard from "../cards/course-card";

import { useCoursesWithLessonCounts } from "@/features/courses/hooks/use-courses-with-lesson-counts";
import { getOffers, getStatus } from "@/features/vizu-pay/services/vizu-pay-service";

export default function CourseGrid() {
  const { data: courses, isLoading } = useCoursesWithLessonCounts();
  // Prices come from the backend (GET /vizu-pay/offers) — never hard-coded.
  const { data: offers } = useQuery({ queryKey: ["vizu-pay-offers"], queryFn: getOffers, staleTime: 5 * 60_000 });
  const { data: status } = useQuery({ queryKey: ["vizu-pay-status"], queryFn: getStatus });

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
        <CourseCard
          key={course.id}
          course={course}
          offer={offers?.find((o) => o.kind === "LEVEL" && o.code === course.level)}
          offerStatus={status}
        />
      ))}
    </section>
  );
}
