"use client";

import { Users } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import ProgressBar from "@/components/ui/progress-bar";
import { useTeacherStudents } from "@/features/teacher/hooks/use-teacher-students";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function TeacherStudentsPage() {
  const { t } = useTranslation();
  const { data: students, isLoading } = useTeacherStudents();

  return (
    <div className="space-y-8">
      <PageHeader
        icon={Users}
        titleKey="teacher.myStudents"
        subtitleKey="teacher.myStudentsSubtitle"
        gradient="from-accent-blue to-purple-600"
      />

      <div className="rounded-card bg-surface-card shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        {isLoading && <p className="p-6 text-sm text-text-muted">{t("common.loading")}</p>}

        {!isLoading && (students?.length ?? 0) === 0 && (
          <p className="p-6 text-center text-sm text-text-secondary">{t("teacher.noStudents")}</p>
        )}

        {!isLoading && (students?.length ?? 0) > 0 && (
          <div className="divide-y divide-surface-border">
            {students!.map((student) => (
              <div key={`${student.id}-${student.course_title}`} className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="truncate text-sm font-bold text-text-primary">{student.name}</p>
                  <p className="truncate text-xs text-text-muted">{student.email}</p>
                </div>
                <div className="flex items-center gap-4 sm:w-64 sm:shrink-0">
                  <span className="shrink-0 rounded-full bg-accent-blue/10 px-2.5 py-1 text-xs font-semibold text-accent-blue">
                    {student.course_level}
                  </span>
                  <div className="min-w-0 flex-1">
                    <ProgressBar value={student.progress} trackClassName="h-1.5" />
                  </div>
                  <span className="shrink-0 text-xs font-bold text-text-secondary">{student.progress}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
