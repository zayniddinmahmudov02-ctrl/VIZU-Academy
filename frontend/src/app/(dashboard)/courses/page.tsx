"use client";

import { GraduationCap } from "lucide-react";

import CourseFilter from "@/components/courses/sections/course-filter";
import CourseGrid from "@/components/courses/sections/course-grid";
import PageHeader from "@/components/dashboard/page-header";
import { totalGermanModules } from "@/constants/levels";

export default function CoursesPage() {
  return (
    <div className="space-y-8">

      <PageHeader
        icon={GraduationCap}
        titleKey="courses.title"
        subtitleKey="courses.subtitle"
        subtitleVars={{ count: totalGermanModules }}
        gradient="from-accent-blue to-purple-600"
      />

      <CourseFilter />

      <CourseGrid />

    </div>
  );
}
