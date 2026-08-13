"use client";

import { useQuery } from "@tanstack/react-query";

import { getLessonsByModule } from "../services/lessons-service";
import { levelsApi } from "../services/levels-service";
import { modulesApi } from "../services/modules-service";
import type { Level } from "../types/content.types";

export interface LevelWithLessonCount extends Level {
  lessonCount: number;
}

/** Admin-side counterpart to the public useCoursesWithLessonCounts — same
 * Course -> Module -> Lessons fan-out, just against the admin CRUD
 * endpoints so /admin/courses can show a real lesson count per level. */
export function useLevelsWithLessonCounts() {
  return useQuery({
    queryKey: ["admin-levels-with-lesson-counts"],
    queryFn: async (): Promise<LevelWithLessonCount[]> => {
      const [levels, modules] = await Promise.all([levelsApi.list(), modulesApi.list()]);
      const sorted = [...levels].sort((a, b) => a.order_index - b.order_index);

      const counts = await Promise.all(
        sorted.map(async (level) => {
          const levelModule = modules.find((m) => m.course_id === level.id);
          if (!levelModule) return 0;
          const lessons = await getLessonsByModule(levelModule.id);
          return lessons.length;
        }),
      );

      return sorted.map((level, i) => ({ ...level, lessonCount: counts[i] }));
    },
  });
}
