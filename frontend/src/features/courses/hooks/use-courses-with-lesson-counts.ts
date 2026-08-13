"use client";

import { useQuery } from "@tanstack/react-query";

import { getLessonsByModule } from "@/features/lessons/services/lesson-service";

import { getCourses, getModules } from "../services/course.service";
import type { Course } from "../types/course";

export interface CourseWithLessonCount extends Course {
  lessonCount: number;
}

/** Real Course rows plus their actual lesson count — the source of truth
 * CourseGrid/CourseCard and the courses page's subtitle now read from
 * instead of the hardcoded COURSE_CONTENT/totalGermanModules constants.
 * Public, unauthenticated. Bounded fan-out (one lesson-count fetch per
 * course) is fine at this scale — a handful of levels, not hundreds. */
export function useCoursesWithLessonCounts() {
  return useQuery({
    queryKey: ["public-courses-with-lesson-counts"],
    queryFn: async (): Promise<CourseWithLessonCount[]> => {
      const [courses, modules] = await Promise.all([getCourses(), getModules()]);
      const active = courses.filter((c) => c.is_active).sort((a, b) => a.order_index - b.order_index);

      const counts = await Promise.all(
        active.map(async (course) => {
          const courseModule = modules.find((m) => m.course_id === course.id);
          if (!courseModule) return 0;
          const lessons = await getLessonsByModule(courseModule.id);
          return lessons.length;
        }),
      );

      return active.map((course, i) => ({ ...course, lessonCount: counts[i] }));
    },
  });
}
