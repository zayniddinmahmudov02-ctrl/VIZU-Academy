"use client";

import { BookOpen, CheckCircle2, ClipboardList, TrendingUp, Users } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import { useTeacherOverview } from "@/features/teacher/hooks/use-teacher-overview";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function TeacherOverviewPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useTeacherOverview();

  return (
    <div className="space-y-8">
      <PageHeader
        icon={Users}
        titleKey="teacher.overviewTitle"
        subtitleKey="teacher.overviewSubtitle"
        gradient="from-accent-blue to-purple-600"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          icon={BookOpen}
          label={t("teacher.assignedCourses")}
          value={isLoading ? "…" : String(data?.assigned_course_count ?? 0)}
        />
        <StatCard
          icon={Users}
          label={t("teacher.totalStudents")}
          value={isLoading ? "…" : String(data?.student_count ?? 0)}
        />
        <StatCard
          icon={TrendingUp}
          label={t("teacher.avgProgress")}
          value={isLoading ? "…" : `${data?.average_progress ?? 0}%`}
        />
        <StatCard
          icon={ClipboardList}
          label={t("teacher.newHomework")}
          value={isLoading ? "…" : String(data?.new_homework_count ?? 0)}
        />
        <StatCard
          icon={ClipboardList}
          label={t("teacher.toGrade")}
          value={isLoading ? "…" : String(data?.to_grade_count ?? 0)}
        />
        <StatCard
          icon={CheckCircle2}
          label={t("teacher.gradedCount")}
          value={isLoading ? "…" : String(data?.graded_count ?? 0)}
        />
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Users;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-4 rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-blue/10 text-accent-blue">
        <Icon size={22} />
      </div>
      <div>
        <p className="text-2xl font-bold text-text-primary">{value}</p>
        <p className="text-sm text-text-secondary">{label}</p>
      </div>
    </div>
  );
}
