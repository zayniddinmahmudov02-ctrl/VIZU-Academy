"use client";

import { BookOpen, CheckCircle2, PlayCircle, XCircle } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import type { LearningAnalytics, NamedCount } from "@/features/admin/types/enterprise-dashboard.types";

function NamedCountRow({ icon: Icon, label, item }: { icon: typeof BookOpen; label: string; item: NamedCount | null }) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-white/[0.02] p-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
        <Icon size={16} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</p>
        <p className="truncate text-sm font-semibold text-[var(--admin-text-primary)]">
          {item ? item.title : "Noch keine Daten"}
        </p>
      </div>
      {item && (
        <span className="shrink-0 rounded-full bg-white/5 px-2 py-1 text-xs font-semibold text-[var(--admin-text-secondary)]">
          {item.count}
        </span>
      )}
    </div>
  );
}

function CompletionRing({ label, percent }: { label: string; percent: number }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-lg bg-white/[0.02] p-4">
      <p className="text-2xl font-bold text-[var(--admin-primary)]">{percent}%</p>
      <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/5">
        <div
          className="h-full rounded-full bg-[var(--admin-primary)] transition-all duration-500"
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </div>
  );
}

export function LearningAnalyticsSkeleton() {
  return (
    <AdminCard className="h-[300px] animate-pulse">
      <div className="h-3 w-40 rounded bg-white/5" />
      <div className="mt-6 grid grid-cols-2 gap-3">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-14 rounded-lg bg-white/5" />
        ))}
      </div>
    </AdminCard>
  );
}

export default function DashboardLearningAnalytics({ data }: { data: LearningAnalytics }) {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Learning Analytics</h3>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <NamedCountRow icon={BookOpen} label="Most Active Course" item={data.most_active_course} />
        <NamedCountRow icon={PlayCircle} label="Most Viewed Lesson" item={data.most_viewed_lesson} />
        <NamedCountRow icon={CheckCircle2} label="Most Solved Quiz" item={data.most_solved_quiz} />
        <NamedCountRow icon={XCircle} label="Most Failed Quiz" item={data.most_failed_quiz} />
      </div>
      <div className="mt-3 flex gap-3">
        <CompletionRing label="Course Completion" percent={data.course_completion_percent} />
        <CompletionRing label="Student Completion" percent={data.student_completion_percent} />
      </div>
    </AdminCard>
  );
}
