"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { EmptyState, ErrorState, Loading, Panel, StudentStatusBadge, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { formatDate, formatDateTime, formatDuration } from "@/features/activity/lib/format";
import { getRosterStudent } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

function Info({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-text-muted">{label}</dt>
      <dd className="text-sm text-text-primary">{value}</dd>
    </div>
  );
}

export default function TeacherStudentProfilePage() {
  const { studentId } = useParams<{ studentId: string }>();
  const { t, language } = useTranslation();
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["teacher-roster-student", studentId], queryFn: () => getRosterStudent(studentId), retry: false });
  const notFound = (error as { response?: { status?: number } } | null)?.response?.status === 404;

  return (
    <div data-testid="teacher-student-profile">
      <Link href="/teacher/students" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue"><ArrowLeft size={16} /> {t("tpanel.back")}</Link>
      {isLoading && <Loading />}
      {isError && (notFound ? <EmptyState text={t("tpanel.emptyStudents")} /> : <ErrorState onRetry={() => refetch()} />)}
      {data && (
        <>
          <TeacherPageTitle title={data.student.name} subtitle={data.student.email} actions={<StudentStatusBadge status={data.student.status} />} />
          <div className="grid gap-4 lg:grid-cols-3">
            <Panel title={t("tpanel.profileBasics")}>
              <dl className="grid grid-cols-2 gap-3">
                <Info label={t("tpanel.colId")} value={<span className="font-mono text-xs">{data.student.id}</span>} />
                <Info label={t("tpanel.username")} value={data.student.username} />
                <Info label={t("tpanel.colRegistered")} value={formatDate(data.student.registered_at, language)} />
                <Info label={t("tpanel.lastLogin")} value={data.student.last_login_at ? formatDateTime(data.student.last_login_at, language) : t("tpanel.never")} />
                <Info label={t("tpanel.colLastActivity")} value={data.student.last_activity_at ? formatDateTime(data.student.last_activity_at, language) : t("tpanel.never")} />
              </dl>
            </Panel>
            <Panel title={t("tpanel.profileGroups")}>
              {data.groups.length === 0 ? <p className="text-sm text-text-muted">—</p> : (
                <ul className="space-y-1.5">
                  {data.groups.map((g) => (
                    <li key={g.id} className="text-sm"><Link href={`/teacher/groups/${g.id}`} className="font-medium text-text-primary hover:text-accent-blue">{g.name}</Link>
                      <span className="text-text-muted"> · {g.level}{g.joined_at ? ` · ${t("tpanel.joined", { date: formatDate(g.joined_at, language) })}` : ""}</span></li>
                  ))}
                </ul>
              )}
              <h3 className="mb-1.5 mt-4 text-xs font-semibold uppercase tracking-wide text-text-muted">{t("tpanel.profileCourses")}</h3>
              <p className="text-sm text-text-secondary">{data.courses.map((c) => `${c.level} · ${c.title}`).join(", ") || "—"}</p>
            </Panel>
            <Panel title={t("tpanel.profileResults")}>
              <dl className="grid grid-cols-2 gap-3">
                <Info label={t("tpanel.homeworkGraded")} value={data.results.homework_graded} />
                <Info label={t("tpanel.homeworkAvg")} value={data.results.homework_average ?? "—"} />
                <Info label={t("tpanel.examsFinished")} value={data.results.exams_finished} />
                <Info label={t("tpanel.bestLevel")} value={data.results.best_level ?? "—"} />
              </dl>
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Panel title={t("tpanel.profileProgress")} testId="profile-progress">
              {data.progress.length === 0 ? <p className="text-sm text-text-muted">{t("tpanel.noProgress")}</p> : (
                <ul className="space-y-3">
                  {data.progress.map((c) => (
                    <li key={c.course_id}>
                      <div className="flex items-baseline justify-between gap-2 text-sm">
                        <span className="font-medium text-text-primary">{c.level} · {c.title}</span>
                        <span className="text-text-secondary">{t("tpanel.lessonsOf", { done: c.lessons_completed, total: c.lessons_total })} · {c.percent}%</span>
                      </div>
                      <div className="mt-1 h-2 overflow-hidden rounded-full bg-surface-hover" role="progressbar" aria-valuenow={c.percent} aria-valuemin={0} aria-valuemax={100}>
                        <div className="h-full rounded-full bg-accent-blue" style={{ width: `${c.percent}%` }} />
                      </div>
                      {c.last_lesson && <p className="mt-1 text-xs text-text-muted">{t("tpanel.lastLesson", { n: c.last_lesson.number })}: {c.last_lesson.title} · {formatDateTime(c.last_lesson.at, language)}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
            <Panel title={t("tpanel.profileRecent")}>
              {data.recent_activity.length === 0 ? <p className="text-sm text-text-muted">{t("tpanel.emptyActivity")}</p> : (
                <ul className="space-y-1.5 text-sm">
                  {data.recent_activity.map((a, i) => (
                    <li key={i} className="flex justify-between gap-2"><span className="text-text-primary">{a.title ?? t(`tpanel.area_${a.area}`)}</span>
                      <span className="shrink-0 text-xs text-text-muted">{formatDateTime(a.at, language)} · {formatDuration(a.seconds, language)}</span></li>
                  ))}
                </ul>
              )}
              <p className="mt-3 text-xs text-text-muted">{t("tpanel.boundaryNote")}</p>
            </Panel>
            <Panel title={t("tpanel.profileHomework")}>
              {data.homework.length === 0 ? <p className="text-sm text-text-muted">{t("tpanel.noHomework")}</p> : (
                <ul className="space-y-2 text-sm">
                  {data.homework.map((h) => (
                    <li key={h.id} className="flex flex-wrap justify-between gap-2">
                      <span className="min-w-0"><span className="block font-medium text-text-primary">{h.title}</span><span className="block text-xs text-text-muted">{h.lesson}</span></span>
                      <span className="text-xs text-text-secondary">{t(`tpanel.hwStatus_${h.status}`)}{h.score !== null ? ` · ${h.score}` : ""} · {formatDate(h.submitted_at, language)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
            <Panel title={t("tpanel.profileExams")}>
              {data.exams.length === 0 ? <p className="text-sm text-text-muted">{t("tpanel.noExams")}</p> : (
                <ul className="space-y-2 text-sm">
                  {data.exams.map((e) => (
                    <li key={e.id} className="flex flex-wrap justify-between gap-2">
                      <span className="font-medium text-text-primary">{e.title}</span>
                      <span className="text-xs text-text-secondary">{e.status}{e.total_score !== null ? ` · ${e.total_score}/${e.max_score ?? "?"}` : ""}{e.level ? ` · ${e.level}` : ""} · {formatDate(e.started_at, language)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}
