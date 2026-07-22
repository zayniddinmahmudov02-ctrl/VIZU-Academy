import CourseCard from "../cards/course-card";

import { germanLevels } from "@/constants/levels";

export default function CourseGrid() {
  return (
    <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
      {germanLevels.map((level) => (
        <CourseCard key={level.code} level={level} />
      ))}
    </section>
  );
}
