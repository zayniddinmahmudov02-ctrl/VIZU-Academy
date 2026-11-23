"use client";

import { useQuery } from "@tanstack/react-query";
import { BookOpen } from "lucide-react";

import { EmptyState, ErrorState, Loading, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { getTeacherCourses } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function TeacherCoursesPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["teacher-courses"], queryFn: getTeacherCourses });

  return (
    <div data-testid="teacher-courses">
      <TeacherPageTitle title={t("tpanel.coursesTitle")} subtitle={t("tpanel.coursesSubtitle")} />
      {isLoading && <Loading />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && data.length === 0 && <EmptyState text={t("tpanel.emptyCourses")} />}
      {data && data.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {data.map((c) => (
            <div key={c.id} className="rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="teacher-course">
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-accent-blue/10 text-sm font-extrabold text-accent-blue">{c.level}</span>
                <div className="min-w-0"><p className="truncate font-semibold text-text-primary">{c.title}</p>
                  {c.assigned && <span className="text-xs font-medium text-success">{t("tpanel.assigned")}</span>}</div>
              </div>
              <p className="mt-3 flex items-center gap-2 text-sm text-text-secondary"><BookOpen size={15} /> {t("tpanel.lessonsCount", { n: c.lessons })} · {t("tpanel.membersOf", { n: c.students })}</p>
              {c.groups.length > 0 && <p className="mt-1 text-xs text-text-muted">{t("tpanel.viaGroups", { groups: c.groups.join(", ") })}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
