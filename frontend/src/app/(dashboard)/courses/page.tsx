"use client";

import { GraduationCap } from "lucide-react";

import CourseFilter from "@/components/courses/sections/course-filter";
import CourseGrid from "@/components/courses/sections/course-grid";
import PageHeader from "@/components/dashboard/page-header";
import { useCoursesWithLessonCounts } from "@/features/courses/hooks/use-courses-with-lesson-counts";

export default function CoursesPage() {
  const { data: courses } = useCoursesWithLessonCounts();
  const totalLessons = (courses ?? []).reduce((sum, c) => sum + c.lessonCount, 0);

  return (
    <div className="space-y-8">

      <PageHeader
        icon={GraduationCap}
        titleKey="courses.title"
        subtitleKey="courses.subtitle"
        subtitleVars={{ count: totalLessons }}
        gradient="from-accent-blue to-purple-600"
      />

      <CourseFilter />

      <CourseGrid />

    </div>
  );
}
