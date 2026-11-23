"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ClipboardCheck, ClipboardList, FileCheck2, Inbox, MonitorPlay, Users, UsersRound } from "lucide-react";

import { EmptyState, ErrorState, Loading, Panel, StatTile, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { formatDateTime } from "@/features/activity/lib/format";
import { getTeacherDashboard } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function TeacherDashboardPage() {
  const { t, language } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["teacher-dashboard"], queryFn: getTeacherDashboard, refetchInterval: 60_000 });

  return (
    <div data-testid="teacher-dashboard">
      <TeacherPageTitle title={t("tpanel.dashTitle")} subtitle={t("tpanel.dashSubtitle")} />
      {isLoading && <Loading />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && (
        <div className="space-y-6">
          {!data.has_groups && (
            <p className="rounded-2xl bg-accent-blue/5 p-4 text-sm text-text-secondary ring-1 ring-accent-blue/15" data-testid="teacher-no-group">{t("tpanel.noGroupYet")}</p>
          )}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <StatTile icon={Users} label={t("tpanel.statStudents")} value={data.stats.students} testId="stat-students" />
            <StatTile icon={UsersRound} label={t("tpanel.statGroups")} value={data.stats.groups} testId="stat-groups" />
            <StatTile icon={BookOpen} label={t("tpanel.statCourses")} value={data.stats.courses} testId="stat-courses" />
            <StatTile icon={MonitorPlay} label={t("tpanel.statLessons")} value={data.stats.lessons} hint={t("tpanel.upcomingHint", { n: data.stats.lessons_upcoming })} testId="stat-lessons" />
            <StatTile icon={ClipboardList} label={t("tpanel.statHomework")} value={data.stats.homework} testId="stat-homework" />
            <StatTile icon={Inbox} label={t("tpanel.statSubmissions")} value={data.stats.new_submissions} testId="stat-submissions" />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Panel title={t("tpanel.upcomingLessons")} testId="dash-upcoming">
              {data.upcoming_lessons.length === 0 ? <EmptyState text={t("tpanel.emptyLessons")} /> : (
                <ul className="space-y-2">
                  {data.upcoming_lessons.map((r) => (
                    <li key={r.id}>
                      <Link href={`/teacher/groups/${r.group_id}?tab=video`} className="flex items-center justify-between gap-3 rounded-xl p-2 hover:bg-surface-hover">
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium text-text-primary">{r.title}</span>
                          <span className="block truncate text-xs text-text-muted">{r.group} · {r.status === "live" ? t("tpanel.live") : formatDateTime(r.scheduled_at, language)}</span>
                        </span>
                        {r.status === "live" && <span className="rounded-full bg-danger/15 px-2 py-0.5 text-xs font-semibold text-danger">LIVE</span>}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title={t("tpanel.groupStatus")} testId="dash-groups">
              {data.groups.length === 0 ? <EmptyState text={t("tpanel.emptyGroups")} /> : (
                <ul className="space-y-2">
                  {data.groups.map((g) => (
                    <li key={g.id}>
                      <Link href={`/teacher/groups/${g.id}`} className="flex items-center justify-between gap-3 rounded-xl p-2 hover:bg-surface-hover">
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium text-text-primary">{g.name} <span className="text-text-muted">· {g.level}</span></span>
                          <span className="block text-xs text-text-muted">{t("tpanel.membersOf", { n: g.students })}{g.capacity ? ` / ${g.capacity}` : ""}</span>
                        </span>
                        <span className="text-xs text-text-muted">{g.status}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title={t("tpanel.recentActivity")} testId="dash-recent">
              {data.recent_activity.length === 0 ? <EmptyState text={t("tpanel.emptyActivity")} /> : (
                <ul className="space-y-2">
                  {data.recent_activity.map((a, i) => (
                    <li key={`${a.student_id}-${i}`}>
                      <Link href={`/teacher/students/${a.student_id}`} className="block rounded-xl p-2 hover:bg-surface-hover">
                        <span className="block truncate text-sm text-text-primary"><span className="font-medium">{a.student}</span> · {a.lesson}</span>
                        <span className="block text-xs text-text-muted">{a.completed ? t("tpanel.completedLesson") : t("tpanel.workedOn")} · {formatDateTime(a.at, language)}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>

            <div className="space-y-4">
              <Panel title={t("tpanel.studentActivity")} testId="dash-activity">
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl bg-success/10 p-3"><p className="text-xl font-bold text-text-primary">{data.students_activity.active_7d}</p><p className="text-xs text-text-secondary">{t("tpanel.active7d")}</p></div>
                  <div className="rounded-xl bg-surface-hover p-3"><p className="text-xl font-bold text-text-primary">{data.students_activity.inactive}</p><p className="text-xs text-text-secondary">{t("tpanel.inactive7d")}</p></div>
                </div>
              </Panel>
              <Panel title={t("tpanel.quickActions")}>
                <div className="grid grid-cols-2 gap-2">
                  {[["/teacher/groups", t("tpanel.quickGroups"), UsersRound], ["/teacher/hausaufgaben", t("tpanel.quickHomework"), ClipboardCheck],
                    ["/teacher/pruefungen", t("tpanel.quickExams"), FileCheck2], ["/teacher/students", t("tpanel.quickStudents"), Users]].map(([href, label, Icon]) => {
                    const I = Icon as typeof Users;
                    return (
                      <Link key={href as string} href={href as string} className="flex items-center gap-2 rounded-xl p-3 text-sm font-medium text-text-primary ring-1 ring-surface-border hover:bg-surface-hover">
                        <I size={16} className="text-accent-blue" /> {label as string}
                      </Link>
                    );
                  })}
                </div>
              </Panel>
            </div>
          </div>

          {!!data.tasks_due.length && (
            <Panel title={t("tpanel.tasksDue")}>
              <ul className="space-y-2">
                {data.tasks_due.map((task) => (
                  <li key={task.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl p-2 text-sm">
                    <span className="text-text-primary">{task.title} <span className="text-text-muted">· {task.group}</span></span>
                    <span className="text-xs text-text-muted">{t("tpanel.due", { date: formatDateTime(task.due_at, language) })} · {t("tpanel.doneOf", { done: task.completed, total: task.students })}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </div>
      )}
    </div>
  );
}
