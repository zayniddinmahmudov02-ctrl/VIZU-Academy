"use client";

import { useQuery } from "@tanstack/react-query";

import { getLessonsByModule } from "@/features/lessons/services/lesson-service";
import type { Lesson } from "@/features/lessons/types/lesson";

import { getCourses, getModules } from "../services/course.service";
import type { Course } from "../types/course";
import type { CourseModule } from "../types/module";

interface LevelCourseResult {
  course: Course | undefined;
  module: CourseModule | undefined;
  lessons: Lesson[];
  isLoading: boolean;
}

/** Resolves one CEFR level (e.g. "A1") to its real Course -> Module ->
 * Lessons, replacing the hardcoded COURSE_CONTENT constant as the source
 * of truth for the level detail page (CourseHero, CourseProgress,
 * ModuleList). Public, unauthenticated — matches GET /courses, GET
 * /modules and GET /lessons/module/{id}, none of which require login. */
export function useLevelCourse(levelCode: string): LevelCourseResult {
  const level = levelCode.toUpperCase();

  const { data: courses, isLoading: coursesLoading } = useQuery({
    queryKey: ["public-courses"],
    queryFn: getCourses,
  });
  const course = courses?.find((c) => c.level === level);

  const { data: modules, isLoading: modulesLoading } = useQuery({
    queryKey: ["public-modules"],
    queryFn: getModules,
  });
  const courseModule = modules?.find((m) => m.course_id === course?.id);

  const { data: lessons, isLoading: lessonsLoading } = useQuery({
    queryKey: ["public-lessons-by-module", courseModule?.id],
    queryFn: () => getLessonsByModule(courseModule!.id),
    enabled: !!courseModule,
  });

  return {
    course,
    module: courseModule,
    lessons: lessons ?? [],
    isLoading: coursesLoading || modulesLoading || (!!course && modulesLoading) || (!!courseModule && lessonsLoading),
  };
}
