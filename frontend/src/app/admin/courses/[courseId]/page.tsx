"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, BookOpen, Settings2 } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import { useCrudList } from "@/features/admin/hooks/use-crud";
import { getLessonsByModule } from "@/features/admin/services/lessons-service";
import { levelsApi } from "@/features/admin/services/levels-service";
import { modulesApi } from "@/features/admin/services/modules-service";

const CONTENT_PANELS = ["Grammatik", "Lesen", "Hören", "Schreiben", "Sprechen", "Wortschatz"];

export default function CourseLessonsPage() {
  const { courseId } = useParams<{ courseId: string }>();

  const { data: courses } = useCrudList("levels", levelsApi);
  const course = courses?.find((c) => c.id === courseId);

  const { data: modules } = useCrudList("modules", modulesApi);
  const module_ = modules?.find((m) => m.course_id === courseId);

  const { data: lessons, isLoading } = useQuery({
    queryKey: ["course-lessons", module_?.id],
    queryFn: () => getLessonsByModule(module_!.id),
    enabled: !!module_,
  });

  const sortedLessons = useMemo(
    () => [...(lessons ?? [])].sort((a, b) => a.number - b.number),
    [lessons],
  );

  return (
    <div>
      <Link
        href="/admin/courses"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Courses
      </Link>

      <AdminPageHeader
        title={course ? `${course.level} — ${course.title}` : "Kurs"}
        description={`${sortedLessons.length} Lektionen · jede mit ${CONTENT_PANELS.join(", ")}`}
      />

      {isLoading && (
        <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>
      )}

      {!isLoading && module_ && sortedLessons.length === 0 && (
        <div className="rounded-2xl bg-[var(--admin-card)] px-6 py-16 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
          <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Lektionen für dieses Level.</p>
        </div>
      )}

      <div className="space-y-2.5">
        {sortedLessons.map((lesson) => (
          <Link
            key={lesson.id}
            href={`/admin/lessons/${lesson.id}`}
            className="flex items-center justify-between gap-4 rounded-2xl bg-[var(--admin-card)] p-4 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)] transition hover:ring-[var(--admin-primary)]/40"
          >
            <div className="flex items-center gap-3.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--admin-primary)]/15 text-xs font-bold text-[var(--admin-primary)]">
                {lesson.number}
              </div>
              <div>
                <p className="font-medium text-[var(--admin-text-primary)]">{lesson.title}</p>
                <p className="flex items-center gap-1 text-xs text-[var(--admin-text-muted)]">
                  <BookOpen size={11} />
                  {CONTENT_PANELS.join(" · ")}
                </p>
              </div>
            </div>
            <Settings2 size={15} className="shrink-0 text-[var(--admin-text-muted)]" />
          </Link>
        ))}
      </div>
    </div>
  );
}
