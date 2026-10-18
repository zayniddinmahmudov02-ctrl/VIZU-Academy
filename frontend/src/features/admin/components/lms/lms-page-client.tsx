"use client";

import { useMemo } from "react";
import Link from "next/link";
import { ChevronRight, FileJson, KeyRound } from "lucide-react";

import { AdminButton, AdminPageHeader } from "@/components/admin/admin-ui";
import { useCrudList } from "@/features/admin/hooks/use-crud";
import { useLevelsWithLessonCounts } from "@/features/admin/hooks/use-levels-with-lesson-counts";
import { languagesApi } from "@/features/admin/services/languages-service";
import { LMS_LEVELS } from "@/features/admin/services/lms-service";

/** LMS -> Kurse -> A1 / A2 / B1 / B2 / C1. One level-agnostic structure:
 * Level -> Modul -> Lektion -> Lesen / Hören / Schreiben / Sprechen. */
export default function LmsPageClient() {
  const { data: languages } = useCrudList("languages", languagesApi);
  const { data: courses, isLoading } = useLevelsWithLessonCounts();

  const languageMap = useMemo(() => new Map((languages ?? []).map((l) => [l.id, l.name])), [languages]);
  const levelCourses = useMemo(
    () =>
      (courses ?? [])
        .filter((c) => (LMS_LEVELS as readonly string[]).includes(c.level))
        .sort((a, b) => LMS_LEVELS.indexOf(a.level as never) - LMS_LEVELS.indexOf(b.level as never) || a.order_index - b.order_index),
    [courses],
  );
  const missing = LMS_LEVELS.filter((lv) => !levelCourses.some((c) => c.level === lv));

  return (
    <div>
      <AdminPageHeader
        title="LMS A1–C1"
        description="Kurse nach Niveau: Module, Lektionen und die vier Fertigkeiten Lesen, Hören, Schreiben, Sprechen."
        action={
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/lms/loesung">
              <AdminButton variant="secondary" data-testid="lms-loesung-link">
                <KeyRound size={16} /> Lösung
              </AdminButton>
            </Link>
            <Link href="/admin/lms/import">
              <AdminButton data-testid="lms-import-link">
                <FileJson size={16} /> Inhalte importieren
              </AdminButton>
            </Link>
          </div>
        }
      />

      {isLoading && <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {levelCourses.map((course) => (
          <Link
            key={course.id}
            href={`/admin/lms/${course.id}`}
            className="group flex items-center justify-between gap-3 rounded-2xl bg-[var(--admin-card)] p-5 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)] transition hover:ring-[var(--admin-primary)]/40"
            data-testid="lms-level-card"
          >
            <div className="flex items-center gap-3.5">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-sm font-bold text-[var(--admin-primary)]">
                {course.level}
              </div>
              <div>
                <p className="font-semibold text-[var(--admin-text-primary)]">{course.title}</p>
                <p className="text-xs text-[var(--admin-text-muted)]">
                  {languageMap.get(course.language_id) ?? "—"}
                  {!course.is_active && " · Inaktiv"}
                </p>
              </div>
            </div>
            <ChevronRight
              size={18}
              className="shrink-0 text-[var(--admin-text-muted)] transition group-hover:translate-x-0.5 group-hover:text-[var(--admin-primary)]"
            />
          </Link>
        ))}
      </div>

      {!isLoading && missing.length > 0 && (
        <p className="mt-6 text-sm text-[var(--admin-text-muted)]">
          Noch kein Kurs für {missing.join(", ")} — unter{" "}
          <Link href="/admin/levels" className="font-semibold text-[var(--admin-primary)] hover:underline">
            Levels
          </Link>{" "}
          anlegen. Der Import kann danach fehlende Module und Lektionen selbst anlegen.
        </p>
      )}
    </div>
  );
}
