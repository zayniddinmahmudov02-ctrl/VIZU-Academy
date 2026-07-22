import { CheckCircle2, Clock3, Trophy } from "lucide-react";

import { COURSE_CONTENT } from "@/constants/course-content";
import type { LevelCode } from "@/constants/levels";

import ProgressBar from "@/components/ui/progress-bar";

interface Props {
  level: LevelCode;
  completedLessons?: number;
  learningHours?: number;
  progress?: number;
}

export default function CourseProgress({
  level,
  completedLessons = 0,
  learningHours = 0,
  progress = 0,
}: Props) {
  const course = COURSE_CONTENT[level];

  return (
    <section className="grid gap-5 md:grid-cols-3">
      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <div className="flex items-center gap-2.5">
          <Clock3 size={18} className="text-accent-blue" />
          <span className="text-sm font-semibold text-text-secondary">
            Lernzeit
          </span>
        </div>

        <h2 className="mt-4 text-3xl font-bold text-text-primary">
          {learningHours} h
        </h2>

        <p className="mt-1.5 text-sm text-text-secondary">
          Gesamte Lernzeit
        </p>
      </div>

      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <div className="flex items-center gap-2.5">
          <CheckCircle2 size={18} className="text-success" />
          <span className="text-sm font-semibold text-text-secondary">
            Abgeschlossen
          </span>
        </div>

        <h2 className="mt-4 text-3xl font-bold text-text-primary">
          {completedLessons} / {course.lessons.length}
        </h2>

        <p className="mt-1.5 text-sm text-text-secondary">
          Unterricht abgeschlossen
        </p>
      </div>

      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <div className="flex items-center gap-2.5">
          <Trophy size={18} className="text-warning" />
          <span className="text-sm font-semibold text-text-secondary">
            Fortschritt
          </span>
        </div>

        <h2 className="mt-4 text-3xl font-bold text-text-primary">
          {progress}%
        </h2>

        <ProgressBar
          value={progress}
          className="mt-4"
        />
      </div>
    </section>
  );
}