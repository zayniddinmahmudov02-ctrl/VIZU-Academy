import CourseHero from "@/components/courses/detail/course-hero";
import CourseProgress from "@/components/courses/detail/course-progress";
import ModuleList from "@/components/courses/detail/module-list";

import type { LevelCode } from "@/constants/levels";

interface Props {
  params: Promise<{
    level: string;
  }>;
}

export default async function CourseDetailPage({ params }: Props) {
  const { level } = await params;

  const courseLevel = level.toUpperCase() as LevelCode;

  return (
    <div className="space-y-8">
      <CourseHero
        level={courseLevel}
        progress={0}
        unlockedLessons={1}
      />

      <CourseProgress level={courseLevel} />

      <ModuleList level={courseLevel} />
    </div>
  );
}