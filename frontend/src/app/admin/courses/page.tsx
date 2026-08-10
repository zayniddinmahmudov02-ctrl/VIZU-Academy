"use client";

import { useMemo } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import { useCrudList } from "@/features/admin/hooks/use-crud";
import { languagesApi } from "@/features/admin/services/languages-service";
import { levelsApi } from "@/features/admin/services/levels-service";
import type { Level } from "@/features/admin/types/content.types";

/** "Courses" — the admin-facing entry point into the existing
 * Language -> Course("Level") -> Module -> Lesson hierarchy (the underlying
 * data is unchanged; this is a new drill-down view over the same
 * `levelsApi`/`modulesApi`/`lessonsApi` already used by the flat
 * /admin/levels, /admin/modules and /admin/lessons CRUD pages). */
export default function CoursesPage() {
  const { data: languages } = useCrudList("languages", languagesApi);
  const { data: courses, isLoading } = useCrudList("levels", levelsApi);

  const languageMap = useMemo(
    () => new Map((languages ?? []).map((l) => [l.id, l.name])),
    [languages],
  );

  const sorted = useMemo(
    () => [...(courses ?? [])].sort((a, b) => a.order_index - b.order_index),
    [courses],
  );

  return (
    <div>
      <AdminPageHeader
        title="Courses"
        description="Sprachniveaus und ihre Lektionen. Struktur und Anzahl entsprechen der öffentlichen Website."
      />

      {isLoading && (
        <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>
      )}

      {!isLoading && sorted.length === 0 && (
        <div className="rounded-2xl bg-[var(--admin-card)] px-6 py-16 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
          <p className="text-sm text-[var(--admin-text-muted)]">
            Noch keine Kurse angelegt.
          </p>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sorted.map((course) => (
          <CourseCard key={course.id} course={course} languageName={languageMap.get(course.language_id)} />
        ))}
      </div>
    </div>
  );
}

function CourseCard({ course, languageName }: { course: Level; languageName?: string }) {
  return (
    <Link
      href={`/admin/courses/${course.id}`}
      className="group flex items-center justify-between gap-3 rounded-2xl bg-[var(--admin-card)] p-5 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)] transition hover:ring-[var(--admin-primary)]/40"
    >
      <div className="flex items-center gap-3.5">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-sm font-bold text-[var(--admin-primary)]">
          {course.level}
        </div>
        <div>
          <p className="font-semibold text-[var(--admin-text-primary)]">{course.title}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">
            {languageName ?? "—"}
            {!course.is_active && " · Inaktiv"}
          </p>
        </div>
      </div>
      <ChevronRight
        size={18}
        className="shrink-0 text-[var(--admin-text-muted)] transition group-hover:translate-x-0.5 group-hover:text-[var(--admin-primary)]"
      />
    </Link>
  );
}
