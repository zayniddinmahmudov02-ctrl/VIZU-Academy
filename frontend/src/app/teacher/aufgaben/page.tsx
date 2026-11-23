"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { EmptyState, ErrorState, Loading, Panel, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { formatDateTime, percent } from "@/features/activity/lib/format";
import { getTeacherTasks } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function TeacherTasksPage() {
  const { t, language } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["teacher-tasks"], queryFn: getTeacherTasks });

  return (
    <div data-testid="teacher-aufgaben">
      <TeacherPageTitle title={t("tpanel.tasksTitle")} subtitle={t("tpanel.tasksSubtitle")} />
      <p className="mb-4 text-sm text-text-muted">{t("tpanel.newTaskHint")}</p>
      {isLoading && <Loading />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && data.length === 0 && <EmptyState text={t("tpanel.emptyTasks")} />}
      {data && data.length > 0 && (
        <Panel>
          <ul className="divide-y divide-surface-border">
            {data.map((task) => {
              const pct = percent(task.completed, task.students) ?? 0;
              return (
                <li key={task.id} className="py-3" data-testid="teacher-task">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="min-w-0"><span className="block font-medium text-text-primary">{task.title}</span>
                      <span className="block text-xs text-text-muted">{task.group} · {task.lesson}</span></span>
                    <span className="text-xs text-text-secondary">{task.due_at ? t("tpanel.due", { date: formatDateTime(task.due_at, language) }) : t("tpanel.noDue")}</span>
                  </div>
                  {task.note && <p className="mt-1 text-sm text-text-secondary">{task.note}</p>}
                  <div className="mt-2 flex items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-hover"><div className="h-full rounded-full bg-accent-blue" style={{ width: `${pct}%` }} /></div>
                    <span className="shrink-0 text-xs text-text-secondary">{t("tpanel.doneOf", { done: task.completed, total: task.students })}</span>
                    <Link href={`/teacher/groups/${task.group_id}?tab=tasks`} className="shrink-0 text-xs font-medium text-accent-blue">{t("tpanel.toGroup")}</Link>
                  </div>
                </li>
              );
            })}
          </ul>
        </Panel>
      )}
    </div>
  );
}
